"""프롬프트 해석 RAG — 비슷한 "정답이 확인된 요청"을 찾아 LLM 지시문에 예시로 붙인다.

왜: LLM(gemma4·OpenAI·Gemini)은 고정 few-shot 몇 개만 본다. 사용자가 "정답 알려주기"로 교정한 표현이나
시드 데이터의 비슷한 문장을 그때그때 찾아 보여주면, LoRA 재학습 없이 교정이 바로 반영된다.

지식 베이스 (우선순위 높은 순 — 같은 문장이면 높은 쪽만 남김)
  1. correction : data/feedback 의 dislike 코멘트가 ParsedPrompt JSON (사용자 교정)
  2. like       : data/feedback 의 like — 시스템 해석을 사용자가 맞다고 확인
  3. seed       : training/lora/seed/train.jsonl (인스턴스 선택·지우기 시드)
  (pipeline_failure·의사 라벨은 정답이 불확실해 넣지 않는다)
  실제로 쓰는 출처는 PROMPT_RAG_SOURCES (기본 correction,like — 시드는 평가에서 정확도를 낮춰 제외)

검색: 글자 2·3-gram TF-IDF 코사인 (한국어 짧은 문장에 맞고 외부 모델·의존성이 필요 없음).
갱신: 피드백 폴더·시드 파일이 바뀌면 PROMPT_RAG_REFRESH_SECONDS 안에 다시 색인.
"""

from __future__ import annotations

import json
import math
import threading
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from loguru import logger

from app.core.config import Settings, get_settings
from app.services.prompt_spec import LLMError, normalize_parsed, parsed_to_json

SOURCE_PRIORITY = {"correction": 3, "like": 2, "seed": 1}


@dataclass(frozen=True)
class Example:
    prompt: str
    answer: str  # parsed_to_json 형식 (정답 JSON 한 줄)
    source: str  # correction | like | seed


@dataclass(frozen=True)
class Hit:
    example: Example
    score: float


# ------------------------------------------------------------------ 텍스트 → 글자 n-gram


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _ngrams(text: str) -> Counter:
    t = f" {_normalize(text)} "
    grams: Counter = Counter()
    for n in (2, 3):
        for i in range(len(t) - n + 1):
            g = t[i : i + n]
            if g.strip():
                grams[g] += 1
    return grams


# ------------------------------------------------------------------ 지식 베이스 적재


def _answer(raw) -> Optional[str]:
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        return parsed_to_json(normalize_parsed(raw)) if isinstance(raw, dict) else None
    except (LLMError, ValueError, TypeError):
        return None


def _comment_json(comment: Optional[str]) -> Optional[str]:
    if not comment or "{" not in comment:
        return None
    text = comment.strip()
    return _answer(text[text.find("{") : text.rfind("}") + 1])


def load_examples(seed_file: Optional[Path], feedback_dir: Optional[Path]) -> list[Example]:
    found: list[Example] = []
    if seed_file and seed_file.is_file():
        for line in seed_file.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            answer = _answer(row.get("parsed_prompt"))
            if isinstance(row.get("prompt"), str) and answer:
                found.append(Example(row["prompt"].strip(), answer, "seed"))

    if feedback_dir and feedback_dir.is_dir():
        for path in sorted(feedback_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            prompt = payload.get("prompt") or meta.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                continue
            source = str(payload.get("source") or meta.get("source") or "user")
            vote = str(payload.get("vote") or "").lower()
            if source == "pipeline_failure":
                continue
            if vote == "dislike":
                answer, kind = _comment_json(payload.get("comment")), "correction"
            elif vote == "like":
                answer, kind = _answer(meta.get("parsed_prompt") or payload.get("parsed_prompt")), "like"
            else:
                continue
            if answer:
                found.append(Example(prompt.strip(), answer, kind))

    # 같은 문장은 우선순위 높은 출처 하나만 (사용자 교정 > 좋아요 > 시드)
    best: dict[str, Example] = {}
    for ex in found:
        key = _normalize(ex.prompt)
        cur = best.get(key)
        if cur is None or SOURCE_PRIORITY[ex.source] >= SOURCE_PRIORITY[cur.source]:
            best[key] = ex
    return list(best.values())


# ------------------------------------------------------------------ 색인 · 검색


class ExampleIndex:
    """글자 n-gram TF-IDF 색인 (메모리, 수천 건 규모)."""

    def __init__(self, examples: Iterable[Example]) -> None:
        self.examples = list(examples)
        docs = [_ngrams(ex.prompt) for ex in self.examples]
        df: Counter = Counter()
        for d in docs:
            df.update(d.keys())
        n = max(1, len(docs))
        self.idf = {g: math.log((1 + n) / (1 + c)) + 1.0 for g, c in df.items()}
        # 지식 베이스에 없는 n-gram 도 질의 벡터에 남겨야 (가장 희귀한 값) 질의의 안 맞는 부분이 점수를 깎는다.
        # 빼 버리면 "왼쪽 세 번째 자전거만 남기고 배경 제거" ↔ "사람만 남기고 배경 제거" 가 0.88 로 뜬다.
        self.unseen_idf = math.log(1 + n) + 1.0
        self.vectors = [self._weigh(d) for d in docs]

    def _weigh(self, grams: Counter) -> dict[str, float]:
        vec = {g: (1 + math.log(c)) * self.idf.get(g, self.unseen_idf) for g, c in grams.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {g: v / norm for g, v in vec.items()}

    def search(self, query: str, k: int = 4, min_score: float = 0.0) -> list[Hit]:
        q = self._weigh(_ngrams(query))
        if not q:
            return []
        scored = []
        for ex, vec in zip(self.examples, self.vectors):
            small, large = (q, vec) if len(q) < len(vec) else (vec, q)
            score = sum(w * large.get(g, 0.0) for g, w in small.items())
            if score >= min_score:
                scored.append(Hit(ex, round(score, 4)))
        # 점수 → 출처 우선순위 (교정이 같은 점수면 먼저)
        scored.sort(key=lambda h: (h.score, SOURCE_PRIORITY[h.example.source]), reverse=True)
        return scored[:k]


def format_examples(hits: list[Hit]) -> str:
    """LLM 지시문 뒤에 붙일 예시 블록."""
    if not hits:
        return ""
    lines = [
        "",
        "Verified examples of similar requests. Follow the rules above first; use these only to see how"
        " similar wording maps to fields. Set each field from the CURRENT request's own words"
        " (e.g. keep position/count only if the current request states them):",
    ]
    for h in hits:
        lines.append(f'"{h.example.prompt}" -> {h.example.answer}')
    return "\n".join(lines)


# ------------------------------------------------------------------ 서비스 싱글톤 (자동 재색인)


class PromptRAG:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._index: Optional[ExampleIndex] = None
        self._signature: Optional[tuple] = None
        self._checked_at = 0.0

    @property
    def sources(self) -> set[str]:
        return {s.strip().lower() for s in self.settings.prompt_rag_sources.split(",") if s.strip()}

    def _paths(self) -> tuple[Optional[Path], Optional[Path]]:
        seed_file = self.settings.prompt_rag_seed_file if "seed" in self.sources else ""
        seed = self.settings.resolve_shared_path(seed_file) if seed_file else None
        return seed, self.settings.feedback_path

    def _source_signature(self) -> tuple:
        seed, fb = self._paths()
        seed_sig = seed.stat().st_mtime_ns if seed and seed.is_file() else 0
        if fb and fb.is_dir():
            files = list(fb.glob("*.json"))
            fb_sig = (len(files), max((f.stat().st_mtime_ns for f in files), default=0))
        else:
            fb_sig = (0, 0)
        return seed_sig, fb_sig

    def index(self) -> ExampleIndex:
        now = time.monotonic()
        with self._lock:
            if self._index is not None and now - self._checked_at < self.settings.prompt_rag_refresh_seconds:
                return self._index
            self._checked_at = now
            sig = self._source_signature()
            if self._index is None or sig != self._signature:
                started = time.perf_counter()
                self._index = ExampleIndex(
                    ex for ex in load_examples(*self._paths()) if ex.source in self.sources
                )
                self._signature = sig
                counts = Counter(ex.source for ex in self._index.examples)
                logger.info(
                    "프롬프트 RAG 색인 {}건 {} ({:.0f} ms)",
                    len(self._index.examples), dict(counts), (time.perf_counter() - started) * 1000,
                )
            return self._index

    def retrieve(self, prompt: str) -> list[Hit]:
        return self.index().search(
            prompt, k=self.settings.prompt_rag_top_k, min_score=self.settings.prompt_rag_min_score
        )


_RAG: Optional[PromptRAG] = None
_RAG_LOCK = threading.Lock()


def get_prompt_rag(settings: Settings | None = None) -> PromptRAG:
    global _RAG
    with _RAG_LOCK:
        if _RAG is None:
            _RAG = PromptRAG(settings or get_settings())
    return _RAG

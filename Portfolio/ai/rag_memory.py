"""안내 챗이 배운 질문과 답을 JSON으로 남긴다.

화면의 대화 목록은 브라우저 localStorage가 가진다.
이 파일은 비슷한 다음 질문을 보완하는 RAG 예시다. 같은 항목을 data/chroma에도 둔다.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path

from rank_bm25 import BM25Okapi

MAX_ITEMS = 200
# 이 점수 이상이면 새 항목 대신 같은 대화의 다른 말투로 붙인다.
MERGE_SCORE = 0.72
# 이 점수 이상일 때만 답변 문맥에 넣는다.
USE_SCORE = 0.34

_LOCK = threading.Lock()


def memory_path() -> Path:
    override = os.environ.get("PORTFOLIO_RAG_MEMORY")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "data" / "rag_memory.json"


def _grams(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[i : i + 2] for i in range(len(compact) - 1)}


def _tokens(text: str) -> list[str]:
    found = re.findall(r"[가-힣]{2,}|[A-Za-z0-9_.:/-]{2,}", text.lower())
    return found or ["empty"]


def _blob(item: dict) -> str:
    parts = [str(item.get("question") or "")]
    parts.extend(str(line) for line in item.get("similar_questions") or [])
    return " ".join(parts)


def _score(query: str, text: str, bm25: float, bm25_top: float) -> float:
    qgrams = _grams(query)
    overlap = len(qgrams & _grams(text)) / len(qgrams) if qgrams else 0.0
    qtokens = set(_tokens(query))
    ttokens = set(_tokens(text))
    recall = len(qtokens & ttokens) / len(qtokens) if qtokens else 0.0
    lexical = float(bm25) / bm25_top if bm25_top else 0.0
    return 0.42 * lexical + 0.36 * overlap + 0.22 * recall


def load_items() -> list[dict]:
    path = memory_path()
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("question") and item.get("answer")]


def _sync_chroma(items: list[dict]) -> None:
    try:
        from chroma_store import sync_memory

        sync_memory(items)
    except Exception:
        return


def _write(items: list[dict]) -> None:
    path = memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "items": items[-MAX_ITEMS:]}
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def search_memory(query: str, k: int = 2, min_score: float = USE_SCORE) -> list[tuple[float, dict]]:
    query = query.strip()
    items = load_items()
    if not query or not items:
        return []
    corpus = [_tokens(_blob(item)) for item in items]
    model = BM25Okapi(corpus)
    raw = model.get_scores(_tokens(query))
    top = max((float(score) for score in raw), default=1.0) or 1.0
    ranked = [
        (_score(query, _blob(item), float(raw[index]), top), item)
        for index, item in enumerate(items)
    ]
    ranked = [item for item in ranked if item[0] >= min_score]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[:k]


def format_examples(hits: list[tuple[float, dict]]) -> str:
    blocks: list[str] = []
    for _, item in hits:
        similar = [str(line).strip() for line in item.get("similar_questions") or [] if str(line).strip()]
        similar_line = " / ".join(similar[:3]) if similar else "(없음)"
        blocks.append(
            "질문: {question}\n비슷한 질문: {similar}\n답: {answer}".format(
                question=str(item.get("question") or "").strip(),
                similar=similar_line,
                answer=str(item.get("answer") or "").strip()[:700],
            )
        )
    return "\n\n".join(blocks)


def _clean_lines(lines: list[str], question: str) -> list[str]:
    kept: list[str] = []
    seen = {question.strip()}
    for line in lines:
        text = re.sub(r"\s+", " ", str(line)).strip(" \n\"'`")
        if not (8 <= len(text) <= 180):
            continue
        if text in seen:
            continue
        seen.add(text)
        kept.append(text)
    return kept[:6]


def remember_exchange(
    question: str,
    answer: str,
    sources: list[str],
    route: str,
    similar_questions: list[str],
) -> str:
    """배운 대화를 저장하고 항목 id를 돌려준다. 아주 비슷한 질문은 같은 항목에 합친다."""
    question = question.strip()
    answer = answer.strip()
    if len(question) < 8 or len(answer) < 40:
        return ""
    if answer.startswith("문서에서는 답을 만들지 못했습니다"):
        return ""
    with _LOCK:
        items = load_items()
        hits = []
        if items:
            corpus = [_tokens(_blob(item)) for item in items]
            model = BM25Okapi(corpus)
            raw = model.get_scores(_tokens(question))
            top = max((float(score) for score in raw), default=1.0) or 1.0
            hits = sorted(
                (
                    (_score(question, _blob(item), float(raw[index]), top), index)
                    for index, item in enumerate(items)
                ),
                reverse=True,
            )
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        if hits and hits[0][0] >= MERGE_SCORE:
            index = hits[0][1]
            current = items[index]
            merged = _clean_lines(
                [question, *similar_questions, *(current.get("similar_questions") or [])],
                str(current.get("question") or ""),
            )
            current["similar_questions"] = merged
            if len(answer) > len(str(current.get("answer") or "")):
                current["answer"] = answer
                current["sources"] = sources[:8]
            current["updated"] = now
            _write(items)
            _sync_chroma(items)
            return str(current.get("id") or "")
        item_id = f"m{len(items) + 1:04d}"
        items.append(
            {
                "id": item_id,
                "question": question,
                "similar_questions": _clean_lines(similar_questions, question),
                "answer": answer,
                "sources": sources[:8],
                "route": route,
                "created": now,
            }
        )
        _write(items)
        _sync_chroma(items)
        return item_id

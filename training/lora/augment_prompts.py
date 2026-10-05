#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""승인된 사용자 문장 증강 — 같은 뜻의 다른 표현을 만들어 LoRA 학습 데이터로.

왜: 실제 사용자 문장은 적다 (승인 수십 건). 그대로 반복 학습하면 문장을 외울 뿐 표현 변화에 약하다.
    같은 요청을 사람들이 다르게 말하는 방식(어순·높임말·동의어·띄어쓰기)을 늘려 일반화한다.

흐름 (정답은 항상 사람이 검수한 원래 정답 — 모델 출력이 아니다)
  1. 학습 DB 의 승인된 문장 (train split) 을 읽는다 (val 은 평가용이라 증강하지 않음)
  2. Ollama(gemma4) 로 문장마다 다른 표현 N 개 생성 — 대상·효과·위치·순서·개수·색·강도는 그대로
  3. **자기 일치 검증**: 만든 표현을 서비스와 같은 파서(Ollama, RAG 없음)로 다시 해석해
     원래 정답과 모든 필드가 같을 때만 남긴다 (뜻이 바뀐 표현 제거)
  4. 평가셋 문장 · 원문 · 중복 제거. 원문이 평가셋 문장이면 아예 증강하지 않는다 (다른 표현도 누수) → JSONL ({"prompt", "parsed_prompt", "origin_sample_id"})

실행 (저장소 루트, training venv, Ollama 실행 중):
  python training/lora/augment_prompts.py --per-sample 6
  → training/outputs/lora/augment/approved_aug.jsonl  (train_lora.py 가 기본으로 읽음)
출력은 사용자 문장에서 나온 데이터라 git 에 올리지 않는다 (training/outputs/ 무시).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_LORA_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _LORA_DIR.parents[1]
for p in (str(_LORA_DIR), str(_REPO_ROOT / "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

from dataset import discover_db_samples, load_eval_prompts, normalize_prompt  # noqa: E402
from eval_parser import score  # noqa: E402

PARAPHRASE_SYSTEM = """You write Korean paraphrases of photo-editing requests for an image app.
Given one request and its exact meaning (JSON), write {n} DIFFERENT natural Korean requests a real user might type
that mean EXACTLY the same thing.

Keep identical: the objects, which object is kept or removed (keep-only vs erase-this), position words
(왼쪽/오른쪽/가운데/맨 앞/뒤/제일 큰/제일 작은), order (두 번째 …), counts (한 명, 2명 …), colors and clothing,
crop, and any intensity number.
Vary: word order, politeness (해줘/해 주세요/부탁해/반말), synonyms (지워/없애/삭제/날려, 남기고/빼고 나머지,
흐리게/블러/뿌옇게), spacing, short vs long phrasing. Do not add new objects or conditions. Do not translate to English.

Return JSON only: {{"paraphrases": ["...", "..."]}}"""


def _call_ollama(system: str, user: str, settings, timeout: float) -> str:
    from app.services.prompt_llm import _post_json

    data = _post_json(
        f"{(settings.llm_base_url or 'http://localhost:11434').rstrip('/')}/api/chat",
        {
            "model": settings.ollama_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.8},
        },
        timeout=timeout,
    )
    return str((data.get("message") or {}).get("content") or "")


def paraphrase(prompt: str, answer: dict, n: int, settings) -> list[str]:
    user = f"Request: {prompt}\nMeaning: {json.dumps(answer, ensure_ascii=False)}"
    try:
        raw = json.loads(_call_ollama(PARAPHRASE_SYSTEM.format(n=n), user, settings, settings.llm_timeout_seconds * 4))
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(f"  생성 실패: {exc}")
        return []
    items = raw.get("paraphrases") if isinstance(raw, dict) else None
    return [s.strip() for s in items or [] if isinstance(s, str) and s.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="승인된 사용자 문장 증강 (자기 일치 검증)")
    ap.add_argument("--per-sample", type=int, default=6, help="문장당 생성 수 (검증 후 줄어듦)")
    ap.add_argument("--sources", default="correction,like,request", help="증강할 승인 샘플 출처")
    ap.add_argument("--eval-file", type=Path, nargs="+",
                    default=[_LORA_DIR / "seed" / "eval.jsonl", _LORA_DIR / "seed" / "eval_ext.jsonl"])
    ap.add_argument("--output", type=Path,
                    default=_REPO_ROOT / "training" / "outputs" / "lora" / "augment" / "approved_aug.jsonl")
    args = ap.parse_args()

    from app.core.config import Settings
    from app.services.prompt_llm import parse_prompt_llm
    from app.services.prompt_spec import parsed_to_json

    settings = Settings.model_validate({"LLM_PROVIDER": "ollama", "LLM_TIMEOUT_SECONDS": 60})
    samples = discover_db_samples(split="train", sources=[s.strip() for s in args.sources.split(",") if s.strip()])
    eval_keys = set().union(*(load_eval_prompts(f) for f in args.eval_file))
    seen = {normalize_prompt(c.prompt) for c in samples if c.prompt}
    print(f"승인 train 문장 {len(samples)}건 → 문장당 {args.per_sample}개 생성 · 자기 일치 검증")

    rows: list[dict] = []
    stats = {"generated": 0, "kept": 0, "dup_or_eval": 0, "meaning_changed": 0}
    started = time.time()
    for case in samples:
        if not case.prompt or not case.parsed_prompt:
            continue
        if normalize_prompt(case.prompt) in eval_keys:
            # 평가셋 문장의 다른 표현을 학습하면 평가가 부풀려진다 (거의 같은 문장 누수)
            print(f"  건너뜀(평가셋 문장)  {case.prompt}")
            continue
        kept_here = 0
        for text in paraphrase(case.prompt, case.parsed_prompt, args.per_sample, settings):
            stats["generated"] += 1
            key = normalize_prompt(text)
            if key in seen or key in eval_keys:
                stats["dup_or_eval"] += 1
                continue
            seen.add(key)
            parsed = parse_prompt_llm(text, settings)  # 서비스와 같은 해석 (RAG 없음)
            pred = json.loads(parsed_to_json(parsed)) if parsed is not None else None
            if not score(pred, case.parsed_prompt)["exact"]:
                stats["meaning_changed"] += 1
                continue
            rows.append({
                "prompt": text,
                "parsed_prompt": case.parsed_prompt,
                "origin_sample_id": case.payload.get("sample_id"),
                "origin_prompt": case.prompt,
            })
            kept_here += 1
        stats["kept"] += kept_here
        print(f"  {kept_here}/{args.per_sample}  {case.prompt}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"\n생성 {stats['generated']} · 채택 {stats['kept']} · 중복/평가셋 {stats['dup_or_eval']} · "
          f"뜻 바뀜 {stats['meaning_changed']} ({time.time() - started:.0f}s)")
    print(f"→ {args.output}")


if __name__ == "__main__":
    main()

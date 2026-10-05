"""학습 데이터 카탈로그 — 피드백 이벤트를 학습 DB 의 feedbacks · learning_samples 로 기록.

원본은 파일 사이드카다 (data/feedback/{case_id}.json · .jpg, data/pseudo_labels/*.json).
DB 에는 이벤트와 "학습에 쓸 수 있는 데이터" 목록(경로·정답 라벨·출처·검수 상태)만 둔다.

- record_feedback()   : 피드백 1건 → feedbacks 1행 + 파생 learning_samples (0~1행)
- sync_from_files()   : 사이드카 중 DB 에 없는 것만 적재 (멱등 — 기동 시 · 학습 DB 복구 시)
- answer_from_feedback: 피드백에서 프롬프트 정답 추출 (RAG 도 같은 규칙 사용)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.feedback import Feedback
from app.models.learning_sample import LearningSample
from app.services.prompt_spec import LLMError, normalize_parsed, parsed_to_json

# 검증(val) 비율 — id 해시로 고정 배정
VAL_EVERY = 10


# ------------------------------------------------------------------ 정답 추출


def parse_answer(raw: Any) -> Optional[dict]:
    """ParsedPrompt 후보(dict 또는 JSON 문자열) → 정규화된 dict. 형식이 틀리면 None."""
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, dict):
            return None
        return json.loads(parsed_to_json(normalize_parsed(raw)))
    except (LLMError, ValueError, TypeError):
        return None


def answer_from_comment(comment: Optional[str]) -> Optional[dict]:
    """dislike 코멘트 안의 정답 JSON (프론트 "정답 알려주기")."""
    if not comment or "{" not in comment:
        return None
    text = comment.strip()
    return parse_answer(text[text.find("{") : text.rfind("}") + 1])


def answer_from_feedback(vote: str, source: str, comment: Optional[str], meta: dict) -> tuple[Optional[dict], Optional[str]]:
    """(정답 dict, 출처 correction|like). 정답이 불확실하면 (None, None).

    pipeline_failure 의 parsed_prompt 는 시스템 해석일 뿐 정답이 아니라 제외한다.
    """
    if source == "pipeline_failure":
        return None, None
    vote = (vote or "").lower()
    if vote == "dislike":
        answer = answer_from_comment(comment)
        return (answer, "correction") if answer else (None, None)
    if vote == "like":
        answer = parse_answer(meta.get("parsed_prompt"))
        return (answer, "like") if answer else (None, None)
    return None, None


def assign_split(sample_id: str) -> str:
    """id 해시로 train/val 고정 배정 (재학습해도 같은 데이터는 같은 쪽)."""
    return "val" if int(hashlib.sha1(sample_id.encode()).hexdigest(), 16) % VAL_EVERY == 0 else "train"


def shared_relpath(path: Optional[Path | str], settings: Settings) -> Optional[str]:
    """저장소 루트 기준 상대 경로 (호스트·Docker 에서 같은 값). 루트 밖이면 절대 경로 그대로."""
    if not path:
        return None
    p = Path(path)
    root = settings.resolve_shared_path(".")
    try:
        return p.resolve().relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


# ------------------------------------------------------------------ 기록


def _samples_for(fb: Feedback, label_path: Optional[str]) -> list[LearningSample]:
    meta = fb.meta or {}
    samples: list[LearningSample] = []
    answer, kind = answer_from_feedback(fb.vote, fb.source, fb.comment, meta)
    if answer and fb.prompt:
        samples.append(
            LearningSample(
                id=uuid4().hex, kind="prompt", source=kind, status="pending", origin_id=fb.id,
                job_id=fb.job_id, user_id=fb.user_id, prompt=fb.prompt, answer=answer,
                image_path=fb.image_path, label_path=label_path,
            )
        )
    if fb.source == "pipeline_failure" and fb.image_path:
        samples.append(
            LearningSample(
                id=uuid4().hex, kind="segment", source="pipeline_failure", status="pending", origin_id=fb.id,
                job_id=fb.job_id, user_id=fb.user_id, prompt=fb.prompt,
                answer=parse_answer(meta.get("parsed_prompt")), image_path=fb.image_path,
                label_path=label_path,
            )
        )
    return samples


def record_feedback(
    db: Session,
    *,
    case_id: str,
    job_id: str,
    vote: str,
    source: str,
    comment: Optional[str],
    meta: dict,
    user_id: Optional[str] = None,
    image_path: Optional[str] = None,
    label_path: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Feedback:
    """feedbacks 1행 + 파생 학습 샘플. 이미 있으면 기존 행을 돌려준다 (멱등)."""
    existing = db.get(Feedback, case_id)
    if existing is not None:
        return existing
    meta = meta or {}
    fb = Feedback(
        id=case_id, job_id=job_id, user_id=user_id, vote=vote, comment=comment, source=source,
        prompt=meta.get("prompt"), image_path=image_path, meta=meta,
    )
    if created_at is not None:
        fb.created_at = created_at
    db.add(fb)
    for sample in _samples_for(fb, label_path):
        if created_at is not None:
            sample.created_at = created_at
        db.add(sample)
    db.commit()
    return fb


# ------------------------------------------------------------------ 사이드카 동기화


def _read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _timestamp(raw: Any) -> Optional[datetime]:
    if not isinstance(raw, str):
        return None
    try:
        ts = datetime.fromisoformat(raw)
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def sync_from_files(db: Session, settings: Settings | None = None) -> dict[str, int]:
    """data/feedback · data/pseudo_labels 사이드카 중 DB 에 없는 것만 적재. 반환: 새로 넣은 건수."""
    settings = settings or get_settings()
    added = {"feedbacks": 0, "pseudo_labels": 0}

    fb_dir = settings.feedback_path
    known = {row[0] for row in db.query(Feedback.id).all()}
    if fb_dir.is_dir():
        for path in sorted(fb_dir.glob("*.json")):
            if path.stem in known:
                continue
            data = _read_json(path)
            if not data:
                continue
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            if not meta.get("prompt") and isinstance(data.get("prompt"), str):
                meta["prompt"] = data["prompt"]
            image = fb_dir / data["image"] if data.get("image") else None
            record_feedback(
                db,
                case_id=str(data.get("case_id") or path.stem),
                job_id=str(data.get("job_id") or path.stem.rsplit("_", 1)[0]),
                vote=str(data.get("vote") or ""),
                source=str(data.get("source") or meta.get("source") or "user"),
                comment=data.get("comment"),
                meta=meta,
                user_id=data.get("user_id"),
                image_path=shared_relpath(image, settings) if image and image.is_file() else None,
                label_path=shared_relpath(path, settings),
                created_at=_timestamp(data.get("timestamp")),
            )
            added["feedbacks"] += 1

    pl_dir = settings.pseudo_label_path
    known_pl = {
        row[0] for row in db.query(LearningSample.origin_id).filter(LearningSample.source == "pseudo_label").all()
    }
    if pl_dir.is_dir():
        for path in sorted(pl_dir.glob("*.json")):
            case_id = path.stem
            if case_id in known_pl:
                continue
            data = _read_json(path)
            if not data:
                continue
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            prompt = data.get("prompt") or meta.get("prompt")
            answer = parse_answer(data.get("parsed_prompt") or meta.get("parsed_prompt"))
            if not isinstance(prompt, str) or not answer:
                continue
            image = pl_dir / data["image"] if data.get("image") else None
            db.add(
                LearningSample(
                    id=uuid4().hex, kind="prompt", source="pseudo_label", status="pending", origin_id=case_id,
                    prompt=prompt, answer=answer,
                    image_path=shared_relpath(image, settings) if image and image.is_file() else None,
                    label_path=shared_relpath(path, settings),
                )
            )
            added["pseudo_labels"] += 1
        db.commit()

    if any(added.values()):
        logger.info("학습 DB 동기화: 피드백 {}건 · 의사 라벨 {}건 추가", added["feedbacks"], added["pseudo_labels"])
    return added

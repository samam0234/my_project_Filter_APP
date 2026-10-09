"""회원 실패 · 확신 낮은 요청의 사진 보관 — 피드백 폴더(FEEDBACK_DIR)의 원본 사진에 보관 기간을 두고, 계정 삭제 때 같이 지운다.

처리에 실패했거나(파이프라인 실패) 확신이 낮은(HARD_EXAMPLE_CONF) 회원 요청은
원인 분석 · 세그 모델 개선(라벨링, scripts/seg_labeling.py)을 위해 원본 사진이 피드백 폴더에 남는다.
예전에는 이 사진이 업로드 정리(24시간) 대상이 아니었고 계정을 지워도 남았다 — 개인정보 처리방침과 맞지 않았다.

  purge_expired(settings)          FEEDBACK_IMAGE_RETENTION_DAYS 가 지난 사진을 지운다 (주기 작업 · 콘솔 정리와 함께)
  purge_user(settings, user_id)    그 회원의 사진을 지우고 사이드카 · 학습 DB 에서 회원 연결을 끊는다 (계정 삭제 때)

사이드카 JSON(요청 문장 · 해석 · 평가)은 남긴다 — 처리방침의 "학습용 요청 문장 · 평가 내용"(익명으로 보관)이다.
학습 DB(feedbacks · learning_samples)의 image_path 도 비워 콘솔이 없는 파일을 가리키지 않게 한다.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Optional

from loguru import logger

from app.core.config import Settings, get_settings

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def _images(folder: Path) -> Iterable[Path]:
    if not folder.is_dir():
        return []
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]


def _forget_image(sidecar: Path, *, unlink_user: bool) -> None:
    """사이드카에서 사진 · (선택) 회원 연결을 지운다. 깨진 JSON 은 그대로 둔다."""
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    payload["image"] = None
    payload["image_removed"] = True
    if unlink_user:
        payload["user_id"] = None
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_db_paths(names: set[str], user_id: Optional[str] = None, ldb=None) -> int:
    """학습 DB 에서 지운 사진을 가리키는 image_path 를 비우고, user_id 가 있으면 피드백의 회원 연결도 끊는다.

    ldb: 호출 측이 이미 연 학습 DB 세션 (계정 삭제 · 테스트). 없으면 새로 연다 (주기 정리).
    """
    if not names and not user_id:
        return 0
    from contextlib import nullcontext

    from app.models.feedback import Feedback
    from app.models.learning_sample import LearningSample

    changed = 0
    try:
        if ldb is None:
            from app.db.learning import learning_session

            ctx = learning_session()
        else:
            ctx = nullcontext(ldb)
        with ctx as ldb:
            for model in (Feedback, LearningSample):
                for row in ldb.query(model).filter(model.image_path.isnot(None)).all():
                    if Path(row.image_path).name in names:
                        row.image_path = None
                        changed += 1
            if user_id:
                ldb.query(Feedback).filter(Feedback.user_id == user_id).update({Feedback.user_id: None}, synchronize_session=False)
            ldb.commit()
    except Exception:
        logger.exception("학습 DB 의 사진 경로 정리 실패 (파일은 지웠음)")
    return changed


def purge_expired(settings: Settings | None = None, *, now: float | None = None, dry_run: bool = False) -> dict:
    """보관 기간이 지난 피드백 사진을 지운다. FEEDBACK_IMAGE_RETENTION_DAYS <= 0 이면 사진을 남기지 않는다(전부 지움)."""
    settings = settings or get_settings()
    folder = settings.feedback_path
    days = settings.feedback_image_retention_days
    limit = (now or time.time()) - max(0.0, days) * 86400
    removed, freed, names = 0, 0, set()
    for img in _images(folder):
        if img.stat().st_mtime > limit:
            continue
        freed += img.stat().st_size
        removed += 1
        names.add(img.name)
        if not dry_run:
            img.unlink(missing_ok=True)
            sidecar = img.with_suffix(".json")
            if sidecar.is_file():
                _forget_image(sidecar, unlink_user=False)
    if names and not dry_run:
        _clear_db_paths(names)
        logger.info("보관 기간({}일) 지난 피드백 사진 정리: {}장 ({:.1f}MB)", days, removed, freed / 1024 / 1024)
    return {"removed_files": removed, "freed_bytes": freed, "retention_days": days, "dry_run": dry_run}


def purge_user(settings: Settings | None, user_id: str, ldb=None) -> dict:
    """계정 삭제 — 그 회원의 피드백 사진을 지우고 사이드카 · 학습 DB 에서 회원 연결을 끊는다."""
    settings = settings or get_settings()
    folder = settings.feedback_path
    removed, names = 0, set()
    if folder.is_dir():
        for sidecar in folder.glob("*.json"):
            try:
                payload = json.loads(sidecar.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if payload.get("user_id") != user_id:
                continue
            image_name = payload.get("image")
            if image_name:
                img = folder / Path(image_name).name
                if img.is_file():
                    img.unlink(missing_ok=True)
                    removed += 1
                    names.add(img.name)
            _forget_image(sidecar, unlink_user=True)
    _clear_db_paths(names, user_id, ldb)
    return {"removed_images": removed}

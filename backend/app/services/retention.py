"""업로드 산출물 보관 기간 정리 + 저장 공간 집계.

scripts/cleanup.py(정기 실행)와 운영 콘솔 "지금 정리"가 같은 함수를 쓴다.
FILE_RETENTION_HOURS 보다 오래된 파일을 지우고 빈 폴더를 없앤다. DB 행(작업·배치 기록)은 남는다 —
사용자 기록 화면은 파일이 없으면 이미지 자리에 안내를 보여 준다.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CleanupResult:
    removed_files: int = 0
    freed_bytes: int = 0
    removed_dirs: int = 0
    dry_run: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def cleanup_dir(path: Path, max_age_hours: float, *, dry_run: bool = False) -> CleanupResult:
    """path 아래에서 수정 시각이 max_age_hours 보다 오래된 파일 삭제 + 빈 하위 폴더 제거.

    dry_run 이면 지울 대상만 센다. path 자체는 지우지 않는다.
    """
    result = CleanupResult(dry_run=dry_run)
    if not path.exists():
        return result
    cutoff = time.time() - max_age_hours * 3600
    # topdown=False: 하위부터 순회해 빈 폴더 rmdir 이 가능하도록
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if name.startswith("."):  # .gitkeep 같은 자리표시 파일은 지우지 않는다 (저장소가 폴더를 기억하게 둔 것)
                continue
            fp = Path(root) / name
            try:
                stat = fp.stat()
                if stat.st_mtime < cutoff:
                    if not dry_run:
                        fp.unlink(missing_ok=True)
                    result.removed_files += 1
                    result.freed_bytes += stat.st_size
            except OSError:
                # 권한·잠금 등으로 실패해도 다음 항목 계속
                pass
        if dry_run:
            continue
        for name in dirs:
            dp = Path(root) / name
            try:
                if not any(dp.iterdir()):
                    dp.rmdir()
                    result.removed_dirs += 1
            except OSError:
                pass
    return result


@dataclass
class AreaUsage:
    name: str
    files: int = 0
    bytes: int = 0
    oldest_hours: float | None = None
    expired_files: int = 0  # 보관 기간이 지나 다음 정리에서 지워질 파일


def _scan(path: Path, name: str, max_age_hours: float, now: float) -> AreaUsage:
    usage = AreaUsage(name=name)
    if not path.exists():
        return usage
    cutoff = now - max_age_hours * 3600
    oldest = None
    for root, _dirs, files in os.walk(path):
        for fname in files:
            try:
                stat = (Path(root) / fname).stat()
            except OSError:
                continue
            usage.files += 1
            usage.bytes += stat.st_size
            oldest = stat.st_mtime if oldest is None else min(oldest, stat.st_mtime)
            if stat.st_mtime < cutoff:
                usage.expired_files += 1
    if oldest is not None:
        usage.oldest_hours = round((now - oldest) / 3600, 1)
    return usage


def storage_usage(upload_root: Path, max_age_hours: float) -> list[dict]:
    """업로드 폴더를 단일 작업 · 배치 · 영상으로 나눠 파일 수·용량·가장 오래된 파일 나이."""
    now = time.time()
    areas = [
        _scan(upload_root / "batches", "batches", max_age_hours, now),
        _scan(upload_root / "videos", "videos", max_age_hours, now),
    ]
    jobs = AreaUsage(name="jobs")
    if upload_root.exists():
        for child in upload_root.iterdir():
            if child.name in {"batches", "videos"}:
                continue
            part = _scan(child, "jobs", max_age_hours, now) if child.is_dir() else None
            if part is None:
                continue
            jobs.files += part.files
            jobs.bytes += part.bytes
            jobs.expired_files += part.expired_files
            if part.oldest_hours is not None:
                jobs.oldest_hours = max(jobs.oldest_hours or 0.0, part.oldest_hours)
    return [asdict(jobs)] + [asdict(a) for a in areas]

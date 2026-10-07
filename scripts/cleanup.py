#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""오래된 업로드 산출물 정리 스크립트.

`backend/data/uploads/` (서비스 런타임) 아래에서 수정 시각이 FILE_RETENTION_HOURS(기본 24시간)
보다 오래된 파일을 삭제하고, 비어 있는 디렉터리도 제거한다.
정리 로직은 backend/app/services/retention.py — 운영 콘솔 "시스템 → 지금 정리" 와 같은 함수.

사용:
  python scripts/cleanup.py            # 삭제
  python scripts/cleanup.py --dry-run  # 지울 대상만 집계

환경변수:
  FILE_RETENTION_HOURS  — 보관 시간(시간 단위, 기본 24)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.retention import cleanup_dir  # noqa: E402


def main() -> None:
    """환경변수로 보관 시간을 읽고 backend/data/uploads 를 정리."""
    hours = float(os.getenv("FILE_RETENTION_HOURS", "24"))
    dry_run = "--dry-run" in sys.argv[1:]
    upload = ROOT / "backend" / "data" / "uploads"
    result = cleanup_dir(upload, hours, dry_run=dry_run)
    verb = "삭제 예정" if dry_run else "삭제"
    print(
        f"{upload} 에서 {hours}시간보다 오래된 파일 {result.removed_files}개 {verb} "
        f"({result.freed_bytes / 1024 / 1024:.1f}MB, 빈 폴더 {result.removed_dirs}개)"
    )


if __name__ == "__main__":
    main()

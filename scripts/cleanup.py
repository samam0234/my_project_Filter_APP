#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""오래된 업로드 산출물 정리 스크립트.

`data/uploads/` 아래에서 수정 시각이 FILE_RETENTION_HOURS(기본 24시간)
보다 오래된 파일을 삭제하고, 비어 있는 디렉터리도 제거한다.

사용:
  python scripts/cleanup.py

환경변수:
  FILE_RETENTION_HOURS  — 보관 시간(시간 단위, 기본 24)
"""

from __future__ import annotations

import os
import time
from pathlib import Path


def cleanup_dir(path: Path, max_age_hours: float) -> int:
    """지정 디렉터리에서 max_age_hours 보다 오래된 파일을 삭제.

    Returns:
        삭제한 파일 개수
    """
    if not path.exists():
        return 0

    # 현재 시각 기준 cutoff 이전 mtime 은 삭제 대상
    cutoff = time.time() - max_age_hours * 3600
    removed = 0

    # topdown=False: 하위부터 순회해 빈 폴더 rmdir 이 가능하도록
    for root, dirs, files in os.walk(path, topdown=False):
        # --- 오래된 파일 삭제 ---
        for name in files:
            fp = Path(root) / name
            try:
                if fp.stat().st_mtime < cutoff:
                    fp.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                # 권한/잠금 등으로 실패해도 다음 항목 계속
                pass

        # --- 비어 있는 하위 디렉터리 제거 ---
        for name in dirs:
            dp = Path(root) / name
            try:
                if not any(dp.iterdir()):
                    dp.rmdir()
            except OSError:
                pass

    return removed


def main() -> None:
    """환경변수로 보관 시간을 읽고 data/uploads 를 정리."""
    hours = float(os.getenv("FILE_RETENTION_HOURS", "24"))
    # scripts/ 의 상위 = 저장소 루트
    root = Path(__file__).resolve().parents[1]
    upload = root / "data" / "uploads"
    n = cleanup_dir(upload, hours)
    print(f"{upload} 에서 {hours}시간보다 오래된 파일 {n}개 삭제")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Delete upload artifacts older than FILE_RETENTION_HOURS (default 24h)."""

from __future__ import annotations

import os
import time
from pathlib import Path


def cleanup_dir(path: Path, max_age_hours: float) -> int:
    if not path.exists():
        return 0
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            fp = Path(root) / name
            try:
                if fp.stat().st_mtime < cutoff:
                    fp.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                pass
        for name in dirs:
            dp = Path(root) / name
            try:
                if not any(dp.iterdir()):
                    dp.rmdir()
            except OSError:
                pass
    return removed


def main() -> None:
    hours = float(os.getenv("FILE_RETENTION_HOURS", "24"))
    root = Path(__file__).resolve().parents[1]
    upload = root / "data" / "uploads"
    n = cleanup_dir(upload, hours)
    print(f"Removed {n} files older than {hours}h from {upload}")


if __name__ == "__main__":
    main()

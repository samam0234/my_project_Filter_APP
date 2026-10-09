#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git 에 없는 큰 모델 파일 받기 (체크섬 확인) — 배포 서버 준비용.

사용 (저장소 루트):
  python scripts/fetch_models.py          # 목록 전부 (지금은 LaMa 208MB)
  python scripts/fetch_models.py lama
Docker: docker exec cut_and_keep-backend-1 python -m app.services.model_fetch
받는 곳: backend/models/ (Docker 는 bind mount 라 호스트에 남는다). 이미 있고 체크섬이 맞으면 건너뛴다.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.model_fetch import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

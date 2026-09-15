#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2 — 오프라인 LoRA 파인튜닝 운영 진입점 (주간 배치 가정).

의도:
  - 입력: data/feedback + data/pseudo_labels
  - 출력: training/outputs/lora/<run>/adapter
  - 학습 로직은 training/lora/train_lora.py 에만 둔다 (중복 금지)

사용:
  python scripts/fine_tune_lora.py --dry-run
  python scripts/fine_tune_lora.py --base-model D:\\models\\gemma-2-2b-it
  python scripts/fine_tune_lora.py --dry-run --epochs 5   # 추가 인자는 train_lora 로 전달
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = REPO_ROOT / "training" / "lora" / "train_lora.py"


def main() -> None:
    """운영 진입점 — 주간 기본 인자를 붙인 뒤 train_lora.py 를 호출한다."""

    if not TRAIN_SCRIPT.is_file():
        raise SystemExit(f"학습 스크립트 없음: {TRAIN_SCRIPT}")

    # =============================================================================
    # [하드코딩 파트] 주간 배치 기본 인자
    # -----------------------------------------------------------------------------
    # [임무] 매주 같은 하이퍼를 고정. 학습 루프는 여기 두지 말 것.
    # [연결] training/lora/train_lora.py
    # [규칙] 경로 하드코딩 금지 — REPO_ROOT 기준. 추가 CLI 가 마지막에 덮어씀.
    # [힌트] weekly = ["--epochs", "3", "--lr", "1e-4", "--rank", "8"]
    # =============================================================================
    # >>> 여기에 주간 기본 인자만 수정 <<<
    weekly = [
        "--epochs",
        "3",
        "--lr",
        "1e-4",
        "--rank",
        "8",
        "--batch",
        "1",
    ]

    # =============================================================================
    # [이미 구현된 구간 · 바이브] subprocess 위임
    # -----------------------------------------------------------------------------
    # 학습 로직 중복 금지. 나머지 argv 는 train_lora 가 파싱한다.
    # =============================================================================
    cmd = [sys.executable, str(TRAIN_SCRIPT), *weekly, *sys.argv[1:]]
    print("fine_tune_lora.py →", " ".join(cmd[1:]), flush=True)
    raise SystemExit(subprocess.call(cmd, cwd=str(REPO_ROOT)))


if __name__ == "__main__":
    main()

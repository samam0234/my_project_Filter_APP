#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoRA fine-tuning 진입점 (Phase 2 스캐폴드).

의도:
  - 피드백/의사라벨 데이터로 가벼운 어댑터 학습
  - 산출물은 training/outputs/lora/ 에 저장 후 서버에 어댑터만 교체

아직 전체 학습 루프는 구현하지 않음. 데이터 경로·하이퍼파라미터 계약만 정의.
실행하면 경로 존재 여부만 출력하고 종료(exit 0)한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA fine-tune (Phase 2 scaffold)")
    parser.add_argument(
        "--feedback-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "feedback",
        help="피드백 이미지+JSON 디렉터리",
    )
    parser.add_argument(
        "--pseudo-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "pseudo_labels",
        help="의사 라벨 디렉터리",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "lora",
        help="어댑터 출력 디렉터리",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    # =============================================================================
    # [하드코딩 파트] LoRA 학습 루프
    # -----------------------------------------------------------------------------
    # [임무] feedback/pseudo → adapter 학습 → outputs/lora
    # [연결] CLI args, data/feedback, data/pseudo_labels (YOLO 본선은 training/yolo)
    # [규칙] Phase2. peft/torch 는 training 의존성. adapter 만 저장 권장.
    # [힌트] build_dataset → inject_lora → train → save_adapter
    # =============================================================================
    # >>> 여기에 학습 루프 작성 <<<
    #
    import json
    from datetime import datetime

    try :
        import torch
        from torch.utils.data import DataLoader
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model, PeftModel
    except ImportError as e:
        print("필수 의존성이 없습니다. training/requirements-training.txt 확인 후 설치하세요.")
        print(f"import error: {e}")
        raise SystemExit(1) from e

    args.output.mkdir(parents=True, exist_ok=True)

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 스캐폴드 안내 출력 후 종료
    # =============================================================================
    print("=== LoRA train (scaffold) ===")
    print(f"feedback_dir = {args.feedback_dir} exists={args.feedback_dir.exists()}")
    print(f"pseudo_dir   = {args.pseudo_dir} exists={args.pseudo_dir.exists()}")
    print(f"output       = {args.output}")
    print(f"epochs={args.epochs} lr={args.lr}")
    print("지금은 스캐폴드만 동작합니다. 위 하드코딩 구간에 학습 루프를 작성하세요.")
    print("YOLO 세그 학습은 training/yolo/ 를 사용하세요.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()

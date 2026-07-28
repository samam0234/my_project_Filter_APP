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

    # --- 스캐폴드: 계약만 출력 (실제 학습 없음) ---
    print("=== LoRA train (scaffold) ===")
    print(f"feedback_dir = {args.feedback_dir} exists={args.feedback_dir.exists()}")
    print(f"pseudo_dir   = {args.pseudo_dir} exists={args.pseudo_dir.exists()}")
    print(f"output       = {args.output}")
    print(f"epochs={args.epochs} lr={args.lr}")
    print()
    print("TODO Phase 2:")
    print("  1) 피드백/의사라벨을 학습용 텐서 데이터셋으로 변환")
    print("  2) peft + 베이스 모델에 LoRA 주입")
    print("  3) 학습 후 adapter 를 outputs/lora 에 저장")
    print("  4) 서빙 경로에 어댑터 핫스왑")
    print()
    print("지금은 스캐폴드만 동작합니다. YOLO 학습은 training/yolo/ 를 사용하세요.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()

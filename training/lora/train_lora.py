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

    # ---
    # 제목 (하드코딩 파트 부분 : [LoRA 학습 루프])
    # [관련 작업 임무 및 역할]
    #   피드백·의사라벨로 가벼운 어댑터를 학습해 outputs/lora 에 저장한다.
    #   완성도 스케치 비전·학습 부족분 + Phase2 LoRA 축.
    # [기능하고 연결된 변수 및 함수]
    #   - CLI: --feedback-dir, --pseudo-dir, --output, --epochs, --lr
    #   - 데이터: data/feedback, data/pseudo_labels
    #   - 서빙 연동(추후): 어댑터 경로 Settings 확장
    #   - 본선 세그 재학습은 training/yolo/train_segment.py (여기와 별개)
    # [작성해야 하는 방식 및 규칙]
    #   1) YOLO-seg 본선 fine-tune 이 우선. LoRA 는 Phase2.
    #   2) 대용량 torch 의존은 training/requirements-training.txt 쪽.
    #   3) 산출물은 전체 모델 복제보다 adapter 가중치만 저장 권장.
    #   4) 경로 없으면 명확히 에러/안내 후 non-zero exit 가능.
    # [코드 방식 힌트]
    #   # dataset = build_dataset(args.feedback_dir, args.pseudo_dir)
    #   # model = load_base(...); model = inject_lora(model)
    #   # train(model, dataset, epochs=args.epochs, lr=args.lr)
    #   # save_adapter(model, args.output)
    # ---
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

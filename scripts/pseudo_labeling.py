#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2 — 피드백 케이스로부터 의사 라벨 생성 (스캐폴드).

의도 파이프라인:
  1) data/feedback/*.json + 이미지 읽기
  2) Grounding DINO + SAM2 등으로 마스크 의사 라벨 생성
  3) data/pseudo_labels/ 에 저장 → LoRA/세그 재학습 입력

현재는 안내만 출력한다. 실제 추론 루프는 Phase 2 구현.

사용:
  python scripts/pseudo_labeling.py
"""

from __future__ import annotations


def main() -> None:
    """의사 라벨링 스캐폴드 — 하드코딩 구간에 본문 작성."""

    # =============================================================================
    # [하드코딩 파트] 의사 라벨 생성 루프
    # -----------------------------------------------------------------------------
    # [임무] feedback 이미지 → 의사 마스크 라벨 → data/pseudo_labels
    # [연결] data/feedback, training/lora·yolo, predict_grounding_sam2 또는 YOLO
    # [규칙] JSON·이미지 짝. YOLO-seg 폴리곤 통일. 실패 건 스킵·로그.
    # [힌트] for meta in feedback: load → model → save_pseudo
    # =============================================================================
    # >>> 여기에 루프 작성 <<<
    #

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 스캐폴드 안내
    # =============================================================================
    print(
        "pseudo_labeling.py: Phase 2 스캐폴드입니다.\n"
        "읽기: data/feedback/*.json + 이미지\n"
        "쓰기: data/pseudo_labels/\n"
        "위 하드코딩 구간에 루프를 작성하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

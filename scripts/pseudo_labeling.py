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
    """의사 라벨링 스캐폴드 안내 출력 후 정상 종료."""
    print(
        "pseudo_labeling.py: Phase 2 스캐폴드입니다.\n"
        "읽기: data/feedback/*.json + 이미지\n"
        "쓰기: data/pseudo_labels/\n"
        "예정 백엔드: Grounding DINO + SAM2"
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

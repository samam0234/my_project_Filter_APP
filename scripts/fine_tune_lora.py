#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2 — 오프라인 LoRA 파인튜닝 스캐폴드 (주간 배치 가정).

의도:
  - 입력: data/feedback + data/pseudo_labels
  - 출력: models/lora 어댑터 가중치 (서버 핫스왑)
  - 실행 환경: 로컬 GPU 또는 Colab 등

본 학습 루프는 `training/lora/train_lora.py` 로 이전·확장 중.
이 파일은 scripts 쪽 단축/운영 진입점 자리 표시용이다.

사용:
  python scripts/fine_tune_lora.py
"""

from __future__ import annotations


def main() -> None:
    """LoRA 스캐폴드 안내 출력 후 정상 종료."""
    print(
        "fine_tune_lora.py: Phase 2 스캐폴드입니다.\n"
        "입력: data/feedback + data/pseudo_labels\n"
        "출력: models/lora 어댑터 가중치 (서버 핫스왑용)\n"
        "본 학습 스크립트: training/lora/train_lora.py 를 참고하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

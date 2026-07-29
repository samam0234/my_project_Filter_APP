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
    """운영 진입점 스캐폴드 — 본 구현은 training/lora/train_lora.py."""

    # =============================================================================
    # [하드코딩 파트] LoRA 운영 진입점 래퍼
    # -----------------------------------------------------------------------------
    # [임무] scripts 에서 train_lora 호출 / 주간 배치 인자 고정
    # [연결] training/lora/train_lora.py (학습 로직 중복 금지)
    # [힌트] subprocess.run([sys.executable, "training/lora/train_lora.py", ...])
    # =============================================================================
    # >>> 여기에 래퍼 작성 <<<
    #

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 스캐폴드 안내
    # =============================================================================
    print(
        "fine_tune_lora.py: Phase 2 스캐폴드입니다.\n"
        "본 학습: training/lora/train_lora.py 하드코딩 구간을 먼저 채우세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

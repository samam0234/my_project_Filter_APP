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

    # ---
    # 제목 (하드코딩 파트 부분 : [LoRA 운영 진입점 래퍼])
    # [관련 작업 임무 및 역할]
    #   scripts 에서 train_lora 를 호출하거나 주간 배치 인자를 고정한다.
    # [기능하고 연결된 변수 및 함수]
    #   training/lora/train_lora.py main, data/feedback, data/pseudo_labels, models/lora
    # [작성해야 하는 방식 및 규칙]
    #   1) 학습 로직 중복 구현 금지 — train_lora 를 subprocess/import 로 호출 권장.
    #   2) 경로·epochs 기본값만 운영 정책에 맞게 고정 가능.
    # [코드 방식 힌트]
    #   # from training.lora.train_lora 를 PATH 에 맞게 호출하거나
    #   # subprocess.run([sys.executable, "training/lora/train_lora.py", ...])
    # ---
    print(
        "fine_tune_lora.py: Phase 2 스캐폴드입니다.\n"
        "본 학습: training/lora/train_lora.py 하드코딩 구간을 먼저 채우세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

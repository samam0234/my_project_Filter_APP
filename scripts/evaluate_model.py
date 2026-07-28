#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""세그멘테이션 품질 평가 스크립트 (스캐폴드).

의도:
  - 라벨이 있는 holdout 셋에서 마스크 IoU, precision/recall 측정
  - 학습(training/) 결과 가중치를 주기적으로 검증

현재는 인터페이스·안내만 출력한다. Phase 2 에서 실제 메트릭 루프 구현 예정.

사용:
  python scripts/evaluate_model.py
"""

from __future__ import annotations


def main() -> None:
    """평가 스캐폴드 안내 출력 후 정상 종료."""
    print(
        "evaluate_model.py: 스캐폴드입니다.\n"
        "예정 메트릭: 마스크 IoU, 대상 클래스 precision/recall\n"
        "입력(예정): 라벨 데이터셋 yaml + 평가 가중치 경로\n"
        "구현 후: training 산출 best.pt 를 여기로 검증하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

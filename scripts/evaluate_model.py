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
    """평가 스캐폴드 — 하드코딩 구간에 메트릭 루프 작성."""

    # =============================================================================
    # [하드코딩 파트] 세그 품질 평가 메트릭
    # -----------------------------------------------------------------------------
    # [임무] holdout 에서 IoU / precision·recall 로 best.pt 검증
    # [연결] training/configs yaml, weights, YOLO 또는 Segmentor
    # [규칙] val only. 클래스별·전체 구분. 데이터/가중치 없으면 명확 exit.
    # [힌트] for img, gt in val: scores.append(iou(pred, gt)); print(mean)
    # =============================================================================
    # >>> 여기에 평가 루프 작성 <<<
    #

    # =============================================================================
    # [이미 구현된 구간 · 바이브] 스캐폴드 안내
    # =============================================================================
    print(
        "evaluate_model.py: 스캐폴드입니다.\n"
        "예정 메트릭: 마스크 IoU, 대상 클래스 precision/recall\n"
        "위 하드코딩 구간에 평가 루프를 작성하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

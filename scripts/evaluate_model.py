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

    # ---
    # 제목 (하드코딩 파트 부분 : [세그 품질 평가 메트릭])
    # [관련 작업 임무 및 역할]
    #   holdout 라벨셋에서 IoU·precision/recall 을 재어 학습 가중치를 검증한다.
    #   비전·학습 루프 완성도 부족분(검증 축).
    # [기능하고 연결된 변수 및 함수]
    #   - 입력: dataset yaml (training/configs), weights path (best.pt)
    #   - 추론: ultralytics YOLO 또는 Segmentor
    #   - 출력: 콘솔 요약 / (선택) JSON 리포트
    # [작성해야 하는 방식 및 규칙]
    #   1) val 이미지만 평가 (train 누수 금지).
    #   2) 클래스별·전체 mIoU 를 구분해 출력하면 재학습 판단에 유리.
    #   3) 가중치 없거나 데이터 없으면 exit code 와 메시지 명확히.
    # [코드 방식 힌트]
    #   # model = YOLO(weights)
    #   # for img, gt_mask in val_loader:
    #   #     pred = model(img); scores.append(iou(pred, gt_mask))
    #   # print(mean(scores))
    # ---
    print(
        "evaluate_model.py: 스캐폴드입니다.\n"
        "예정 메트릭: 마스크 IoU, 대상 클래스 precision/recall\n"
        "위 하드코딩 구간에 평가 루프를 작성하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

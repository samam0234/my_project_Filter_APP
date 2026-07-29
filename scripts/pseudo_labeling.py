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

    # ---
    # 제목 (하드코딩 파트 부분 : [의사 라벨 생성 루프])
    # [관련 작업 임무 및 역할]
    #   실패 피드백 이미지에서 마스크 의사 라벨을 만들어 재학습 입력으로 저장한다.
    #   비전·학습 루프 완성도 부족분(데이터 생산 축).
    # [기능하고 연결된 변수 및 함수]
    #   - 읽기: data/feedback/*.json + 이미지
    #   - 쓰기: data/pseudo_labels/
    #   - 소비: training/lora, training/yolo 데이터 변환
    #   - 백엔드 후보: predict_grounding_sam2 또는 기존 YOLO
    # [작성해야 하는 방식 및 규칙]
    #   1) feedback JSON 메타(prompt, job_id)와 이미지 경로를 짝지을 것.
    #   2) 라벨 포맷은 YOLO-seg 폴리곤 또는 프로젝트 합의 포맷으로 통일.
    #   3) 실패 건은 스킵·로그, 전체 스크립트는 가능하면 끝까지 순회.
    # [코드 방식 힌트]
    #   # for meta_path in Path("data/feedback").glob("*.json"):
    #   #     img = load(...); mask = model(...); save_pseudo(...)
    # ---
    print(
        "pseudo_labeling.py: Phase 2 스캐폴드입니다.\n"
        "읽기: data/feedback/*.json + 이미지\n"
        "쓰기: data/pseudo_labels/\n"
        "위 하드코딩 구간에 루프를 작성하세요."
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()

# Training: Phase 1 Pipeline

## 학습 목표

프롬프트 → 구조화 → 전처리 → 세그 → 효과 → 검증 → 저장 흐름 이해

## 핵심 모듈

- `workflows/nodes.py` — 오케스트레이션
- `services/image_processor.py` — CLAHE 등
- `services/effects.py` — blur/crop/remove_bg
- `services/segmentation.py` — YOLO 또는 stub

## 실습 아이디어

1. stub 마스크로 end-to-end 성공 확인
2. CLAHE clipLimit 변경 후 시각 비교
3. quality threshold 조정 시 fallback 빈도 관찰

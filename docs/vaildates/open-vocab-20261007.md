# 오픈 보캐브(Grounding DINO + SAM2) 실가동 확인 — 2026-10-07

COCO 80 클래스 밖 대상("shirt", "helmet")이 YOLO 대신 Grounding DINO + SAM2 로 처리되는지 확인했다.

## 준비
- 가중치(로컬 HF 캐시, 허브 다운로드는 코드가 하지 않음 — `local_files_only`)
  - `IDEA-Research/grounding-dino-tiny`, `facebook/sam2-hiera-tiny` (`huggingface_hub.snapshot_download`)
- 환경: `training/.venv` (transformers 5.17, torch 2.11+cu128, CUDA)
- 켜기: `OPEN_VOCAB_ENABLED=true` (기본 false 유지 — 가중치가 있는 환경에서만)

## 결과 (coco_val 000000000872.jpg, 사람 2명)
| 대상 | backend | 마스크 면적(px) | 인스턴스 | 시간 |
|------|---------|----------------|---------|------|
| person (COCO 안) | yolo | 67,723 | 2 | 8.6s (모델 첫 로드 포함) |
| shirt (COCO 밖) | dino_sam2 | 18,733 | 2 | 16.4s (DINO·SAM2 첫 로드 포함) |
| helmet (COCO 밖) | dino_sam2 | 4,647 | 2 | 0.8s (로드 후) |

- "닫힌 어휘 밖일 때만" 오픈 보캐브로 가는 분기가 의도대로 동작 (person 은 YOLO 유지)
- 로드 후 호출은 1초 미만. 첫 요청만 느리므로 운영에서는 시작 시 워밍업을 고려

## 주의
- 로드 시 경고: `sam2_video` 체크포인트를 `Sam2Model` 로 여는 transformers 경고 — 동작에는 영향 없음 확인
- helmet 은 해당 이미지에 헬멧이 없을 가능성이 높은데 면적 4,647px 의 인스턴스 2개가 검출됨 → 오검출 가능. 임계값(`threshold`)·정답 이미지 기반 평가는 아직 하지 않았다
- Docker 슬림 이미지(onnx)에는 transformers 가 없어 이 경로를 쓸 수 없다 (GPU 이미지·가중치 볼륨 필요)

# scripts — 유틸 · 학습 · 유지보수 스크립트

백엔드 런타임 밖에서도 돌리는 **오프라인/운영 보조** 스크립트 모음이다.

## 목록

| 스크립트 | 용도 |
|----------|------|
| `convert_to_onnx.py` | YOLO 가중치 → ONNX 변환 |
| `cleanup.py` | 오래된 업로드 파일 삭제 (보관 시간). **백엔드가 매시간 자동으로 같은 정리를 한다** — 손으로 돌릴 때만 |
| `fetch_models.py` | git 에 없는 큰 모델(LaMa) 받기 + SHA-256 확인 — 배포 서버 준비용 (백엔드도 기동 시 자동으로 받음) |
| `send_test_mail.py` | 지금 SMTP 설정으로 테스트 메일 한 통 |
| `export_stuff_onnx.py` | 배경 덩어리용 SegFormer → ONNX (`backend/models/segformer-ade.onnx`) |
| `pseudo_labeling.py` | Phase 2 의사 라벨링 스캐폴드 |
| `deploy_check.py` | 배포 리허설 점검: `remote URL`(인증서 · 리디렉트 · 보안 헤더 · /health · 인증 · CORS · 약관) · `server`(.env 운영 값 · 모델 · 체크섬 · 백업 · Docker) |
| `models_bundle.py` | 설정이 쓰는 모델만 tar 로 묶고 SHA-256 목록 (`pack`), 서버에서 대조 (`verify`) |
| `seg_labeling.py` | 세그 실패 사진 라벨링 묶음: `export`(실패 · 싫어요 사진 + yolo26x 초벌 폴리곤 + Label Studio 가져오기 파일) · `check`(고친 라벨 검사, 클래스 순서 `--fix`) → `retrain_yolo.py --extra` |
| `retrain_yolo.py` | 세그 모델 재학습 루프: COCO 어려운 사례(맞닿은 인스턴스) + 일반 사진 수집 → 이어 학습 → 섞임 평가 · mask mAP 로 배포 모델과 비교 → 판정 (`--deploy` 로 교체, `--extra` 로 직접 라벨링한 사진 추가) |
| `retrain_lora.py` | 승인 사용자 문장이 기준 이상 쌓이면 증강·학습·평가·배포본 비교 (`--deploy` 로 교체) |
| `fine_tune_lora.py` | Phase 2 LoRA 주간 배치 래퍼 (`training/lora/train_lora.py` 호출) |
| `evaluate_model.py` | 모델 평가 스캐폴드 |
| `experiments/selection_e2e.py` | 실제 이미지에서 위치·크기 인스턴스 선택 정확도 (정답 폴리곤) |
| `experiments/refine_speed.py` | GrabCut 정제 전체 vs ROI 속도·정답 IoU |
| `experiments/onnx_vs_pt.py` | 직접 구현한 ONNX 추론이 `.pt` · Ultralytics ONNX 와 얼마나 같은지 (마스크 IoU · 정답 대비) — `docs/plan/ONNX_INFERENCE.md` |
| `experiments/seg_model_compare.py` | 세그 모델 공정 비교 (COCO val2017, 검출률·오검출·선택 정확도) — `docs/plan/YOLO26M_DEFAULT.md` |
| `experiments/ui_check.py` | 브라우저 직접 확인 9개 흐름 (Playwright, 테스트 계정 자동 정리) — `docs/vaildates/ui-check-20261006.md` |
| `experiments/load_test.py` | 동시 업로드 부하 (실서버 필요) — 결과는 `docs/vaildates/experiments-20261006.md` |
| `experiments/leak_eval.py` | 지정하지 않은 대상이 섞이는 정도 (COCO 정답 주석) — `docs/vaildates/leak-diagnosis-20261008.md` |
| `experiments/parse_rounds.py` | 문장 해석 평가 (파서별 · 라운드별 · 다수결) |
| `experiments/edge_quality.py` | 경계 품질 · 영상 흔들림 — `docs/vaildates/edge-tuning-20261008.md` |
| `experiments/stuff_seg_compare.py` | SegFormer 크기 비교 — `docs/vaildates/stuff-segmentation-20261008.md` |
| `experiments/dino_threshold.py` | 오픈 보캐브 박스 임계값 — `docs/vaildates/open-vocab-20261007.md` |
| `experiments/inpaint_eval.py` | 지우기 메우기 Telea vs LaMa (정답 있는 구멍) — `docs/vaildates/inpaint-20261009.md` |

## 사용 예

```powershell
cd d:\my_project\CutNKeep

# 백엔드 venv 활성화 권장
.\backend\.venv\Scripts\activate

python scripts/convert_to_onnx.py --weights models/yolo26m-seg.pt --out models/yolo26m-seg.onnx
python scripts/cleanup.py
```

환경변수 `FILE_RETENTION_HOURS` 는 cleanup 에 영향 (기본 24). 자동 정리 주기는 `FILE_CLEANUP_MINUTES`(백엔드).

## 주의

- `pseudo_labeling.py` / `evaluate_model.py` 는 아직 **스캐폴드**다. 실행 전 docstring 확인.
- `fine_tune_lora.py` 는 `training/lora/train_lora.py` 래퍼. 먼저 `--dry-run`.
- 모델 파일(`.pt`, `.onnx`)은 용량 때문에 gitignore 대상이다. `models/` 에 직접 배치.

## 학습 구역 이전 안내

YOLO/LoRA **본 학습**은 `training/` 을 사용한다.

| 예전 (scripts) | 새 위치 |
|----------------|---------|
| `convert_to_onnx.py` | `training/yolo/export_onnx.py` |
| `fine_tune_lora.py` | `training/lora/train_lora.py` |
| (세그/디텍트 train) | `training/yolo/train_*.py` |

`scripts/` 의 cleanup 등 **운영 유틸**은 그대로 유지.

## 관련 문서

- `training/README.md`
- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/LOGIC_STRUCTURE.md` (피드백 → LoRA 루프)

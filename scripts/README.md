# scripts — 운영 · 배포 · 학습 · 실험 스크립트

> 백엔드 요청 경로 **밖에서** 사람이 직접 돌리는 도구 모음. 서버를 준비하고, 점검하고, 모델을 다시 학습하고, 실험으로 수치를 만든다.

이 폴더의 스크립트는 API가 부르지 않는다. 운영자 · 개발자가 필요할 때 실행한다.
모두 **저장소 루트에서** 실행하는 것을 기준으로 한다.

```bash
# 저장소 루트의 venv (백엔드와 같은 의존성)
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python scripts/<스크립트>.py --help
```

| 묶음 | 하는 일 |
|------|---------|
| [1. 배포 · 점검](#1-배포--점검) | 운영 `.env` 만들기 · 서버 점검 · 모델 묶음 · PC Ollama 터널 · 메일 |
| [2. 모델 준비](#2-모델-준비) | 큰 모델 받기 · ONNX 변환 · SegFormer 내보내기 |
| [3. 유지보수](#3-유지보수) | 업로드 정리 · Chroma 색인 |
| [4. 재학습 루프](#4-재학습-루프) | LoRA · YOLO 재학습 · 실패 사진 라벨링 · 의사 라벨 |
| [5. 실험](#5-실험) | 수치의 근거 — 해석 · 세그 · 선택 · 영상 · 지우기 · UI · 부하 |

---

## 1. 배포 · 점검

| 스크립트 | 용도 |
|----------|------|
| `make_prod_env.py` | 운영 `.env.production` 만들기 — 운영 값 · **새 비밀 값** · 기동 전 점검. `--check <파일>`로 기존 파일만 점검, `--force`는 덮어쓴다(비밀 값이 바뀐다) |
| `deploy_check.py` | 배포 리허설 점검. `remote URL` — 인증서 · http→https · 보안 헤더 · `/health` · DB · 로그인 없는 `/auth/me` 401 · Swagger 비노출 · CORS · 약관. `server` — `.env` 운영 값 · 모델 · 체크섬 · 백업 · Docker (`--gpu`, `--env-file`, `--models-manifest`) |
| `models_bundle.py` | 설정이 쓰는 모델만 tar로 묶고 SHA-256 목록을 만든다 (`pack`, `--gpu`면 LoRA 베이스까지 약 3GB), 서버에서 대조 (`verify`) |
| `ollama_tunnel.sh` | **PC의 Ollama를 서버가 쓰게** SSH 역방향 터널(PC 11434 → 서버 loopback 11435)을 열고, 끊기면 5초마다 재연결 |
| `set_smtp_local.sh` | 이 PC의 `.env`에 SMTP 설정 — 앱 비밀번호는 **숨겨서** 입력받는다 |
| `send_test_mail.py` | 지금 SMTP 설정으로 테스트 메일 한 통 |

```bash
# 공개 서버 점검 — 실패 0 · 경고 0 이어야 한다
python scripts/deploy_check.py remote https://168-110-17-193.sslip.io
# Windows 콘솔에서 ✓ 표시가 cp949 로 깨지면
PYTHONIOENCODING=utf-8 python scripts/deploy_check.py remote https://168-110-17-193.sslip.io

# 운영 env 만들기 · 점검
python scripts/make_prod_env.py --domain cutnkeep.example.com --acme-email you@example.com
python scripts/make_prod_env.py --check .env.production

# 모델 묶어 옮기기
python scripts/models_bundle.py pack            # → dist/models.tar + 체크섬 목록
python scripts/models_bundle.py verify <목록>   # 서버에서

# PC Ollama 터널 — 이 창이 열려 있어야 서버의 AI 해석이 동작한다
CNK_SSH_KEY=<개인키 파일 경로> CNK_SSH_HOST=ubuntu@<서버IP> bash scripts/ollama_tunnel.sh
```

**비밀 값을 다루는 스크립트**(`make_prod_env.py` · `set_smtp_local.sh` · `ollama_tunnel.sh`)는 값을 화면 · 저장소 · 로그에 출력하지 않는다. 개인키는 경로만 받고 내용을 읽어 옮기지 않는다.

---

## 2. 모델 준비

| 스크립트 | 용도 |
|----------|------|
| `fetch_models.py` | Git에 없는 큰 모델(LaMa)을 받고 SHA-256 확인 — 배포 서버 준비용. 백엔드도 기동 시 자동으로 받는다(`MODEL_AUTO_DOWNLOAD`) |
| `convert_to_onnx.py` | YOLO 가중치 → ONNX (torch 없이 onnxruntime으로 서빙할 때) |
| `export_stuff_onnx.py` | 배경 덩어리용 SegFormer → ONNX (`backend/models/segformer-ade.onnx` + 라벨 JSON) |

```bash
python scripts/fetch_models.py
python scripts/convert_to_onnx.py --weights models/yolo26m-seg.pt --out models/yolo26m-seg.onnx
python scripts/export_stuff_onnx.py
```

본 학습 산출물의 ONNX 변환은 `training/yolo/export_onnx.py`도 있다.

---

## 3. 유지보수

| 스크립트 | 용도 |
|----------|------|
| `cleanup.py` | 보관 기간(`FILE_RETENTION_HOURS`, 기본 24)이 지난 업로드 삭제. **백엔드가 매시간(`FILE_CLEANUP_MINUTES`) 같은 정리를 자동으로 한다** — 손으로 돌릴 때만 |
| `chroma_feedback.py` | `data/feedback`의 교정 · 좋아요를 `data/chroma`(컬렉션 `verified_feedback`)에 색인. 의사 라벨 · 실패 사진은 넣지 않는다. `--query "문장"`으로 가까운 예시 확인 |
| `chroma_embed.py` | Chroma 공용 글자 벡터 — 한글 2 · 3글자 조각을 256차원으로 해싱. **임베딩 모델을 받지 않는다.** 백엔드 · 이 폴더 · 포트폴리오 안내가 같은 이름(`cutnkeep-char-ngram`)과 차원을 써서 서로 읽을 수 있다 |

```bash
python scripts/cleanup.py
python scripts/chroma_feedback.py --query "가운데 사람만 남기고 배경 블러"
```

---

## 4. 재학습 루프

운영 콘솔에서 **승인된** 데이터만 학습에 쓴다. 재학습 결과는 배포 중인 모델과 비교해 나아졌을 때만 `--deploy`로 교체한다.

| 스크립트 | 용도 |
|----------|------|
| `retrain_lora.py` | 승인된 사용자 문장이 기준(`LORA_RETRAIN_MIN_NEW`, 200) 이상 쌓이면 증강 · 학습 · 평가 세트 판정 · 배포본 비교. `--deploy`로 교체 |
| `retrain_yolo.py` | 세그 재학습 — COCO 어려운 사례(맞닿은 인스턴스) + 일반 사진 수집 → 이어 학습 → 섞임 평가 · mask mAP로 배포 모델과 비교 → 판정. `--deploy`로 교체, `--extra`로 직접 라벨링한 사진 추가 |
| `seg_labeling.py` | 세그 실패 사진 라벨링 묶음. `export` — 실패 · 싫어요 사진 + yolo26x 초벌 폴리곤 + Label Studio 가져오기 파일. `check` — 고친 라벨 검사, 클래스 순서 `--fix`. 외부 라벨 서비스에는 올리지 않는다 |
| `pseudo_labeling.py` | 오픈 보캐브로 라벨 후보 만들기 (스캐폴드) |
| `fine_tune_lora.py` | LoRA 주간 배치 래퍼 — `training/lora/train_lora.py`를 부른다. 먼저 `--dry-run` |
| `evaluate_model.py` | 모델 평가 스캐폴드 |

```text
실패 사진 ─▶ seg_labeling.py export ─▶ Label Studio 에서 고침 ─▶ seg_labeling.py check ─▶ retrain_yolo.py --extra
승인 문장 ─▶ (200건 이상) ─▶ retrain_lora.py ─▶ 배포본보다 나으면 --deploy
```

기록상 COCO만 추가한 세그 재학습은 채택되지 않았다. 실패 사진이 쌓인 뒤의 재학습이 의미가 있다.
`backend/app/services/prompt_spec.py`를 바꾸면 LoRA를 다시 학습해야 한다 (지시문과 정답 형식이 그 파일이다).

---

## 5. 실험

문서에 적힌 수치는 이 스크립트들의 결과다. 결과 문서는 `docs/vaildates/`에 있다.

| 스크립트 | 무엇을 재나 | 결과 문서 |
|----------|-------------|-----------|
| `experiments/parse_rounds.py` | 문장 해석 — 파서별 · 라운드별 · 다수결 | `docs/vaildates/` |
| `experiments/parser_compare.py` | 해석기 비교 — 지금 체인(Ollama + 키워드) vs LoRA vs 섞은 체인 | `docs/vaildates/parser-compare-20261009.md` |
| `experiments/selection_e2e.py` | 실제 이미지에서 위치 · 크기 인스턴스 선택 정확도 (정답 폴리곤) | |
| `experiments/seg_model_compare.py` | 세그 모델 공정 비교 (COCO val2017 — 검출률 · 오검출 · 선택 정확도) | `docs/plan/YOLO26M_DEFAULT.md` |
| `experiments/onnx_vs_pt.py` | 직접 구현한 ONNX 추론이 `.pt` · Ultralytics ONNX와 얼마나 같은지 | `docs/plan/ONNX_INFERENCE.md` |
| `experiments/leak_eval.py` | 지정하지 않은 대상이 섞이는 정도 (COCO 정답 주석) | `docs/vaildates/leak-diagnosis-20261008.md` |
| `experiments/refine_speed.py` | GrabCut 정제 전체 vs ROI 속도 · 정답 IoU | |
| `experiments/edge_quality.py` | 경계 품질 · 영상 흔들림 | `docs/vaildates/edge-tuning-20261008.md` |
| `experiments/stuff_seg_compare.py` | SegFormer 크기 비교 | `docs/vaildates/stuff-segmentation-20261008.md` |
| `experiments/dino_threshold.py` | 오픈 보캐브 박스 임계값 | `docs/vaildates/open-vocab-20261007.md` |
| `experiments/inpaint_eval.py` | 지우기 메우기 Telea vs LaMa (정답 있는 구멍) | `docs/vaildates/inpaint-20261009.md` |
| `experiments/gif_matte_eval.py` | GIF 배경 제거 경계 — 밝은 · 어두운 배경 매트 효과 | `docs/vaildates/` |
| `experiments/video_tracking_eval.py` | 영상 · GIF 대상 따라가기 — 프레임마다 다시 고르기 vs 처음 고른 인스턴스 추적 (서로 지나가는 합성 영상) | `docs/vaildates/` |
| `experiments/davis_eval.py` | **실제 영상**(DAVIS 2017)으로 추적 · 영상 기능 검증 — 72.8% → 92.1%의 근거 | `docs/vaildates/` |
| `experiments/video_removal_eval.py` | 영상 · GIF 지우기 — 프레임마다 Telea vs 배경판 | `docs/vaildates/` |
| `experiments/ui_check.py` | 브라우저 직접 확인 흐름 (Playwright, 테스트 계정 자동 정리) | `docs/vaildates/ui-check-20261006.md` |
| `experiments/load_test.py` | 동시 업로드 부하 (실서버 필요) | `docs/vaildates/experiments-20261006.md` |

데이터셋(COCO · DAVIS)은 `training/datasets/` 아래에 두고 Git에 올리지 않는다. 실험이 계정을 만들면 끝날 때 지운다.

---

## 주의

- `pseudo_labeling.py` · `evaluate_model.py`는 아직 **스캐폴드**다. 실행 전 docstring을 확인한다.
- 모델 파일(`.pt` · `.onnx`)은 용량 때문에 Git에 올리지 않는다. 원본은 루트 `models/`, 서빙 중인 것은 `backend/models/`.
- YOLO · LoRA **본 학습**은 [`training/`](../training/README.md)에서 한다. 이 폴더는 운영 유틸과 재학습 루프 · 실험이다.

| 예전 (scripts) | 지금 위치 |
|----------------|-----------|
| `convert_to_onnx.py` (본 학습 산출물) | `training/yolo/export_onnx.py` |
| `fine_tune_lora.py` 의 본체 | `training/lora/train_lora.py` |
| 세그 / 디텍트 학습 | `training/yolo/train_*.py` |

## 관련 문서

- [`training/README.md`](../training/README.md) — 학습 구역
- [`docs/guidance/learning-loop.md`](../docs/guidance/learning-loop.md) — 승인 데이터가 RAG · LoRA로 들어가는 경로
- [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) — 배포 순서
- [`docs/guidance/ollama-server.md`](../docs/guidance/ollama-server.md) — PC Ollama 터널
- [`docs/vaildates/README.md`](../docs/vaildates/README.md) — 실험 결과 모음

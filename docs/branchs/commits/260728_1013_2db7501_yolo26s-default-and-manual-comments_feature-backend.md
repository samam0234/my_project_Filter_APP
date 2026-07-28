# docs(yolo): YOLO26s를 기본 비전 모델로 통일 / `2db7501`

> 브랜치: `feature/backend`  
> 작성일: `2026-07-28 10:13`  
> 작성자: Grok agent  
> 파일명: `260728_1013_2db7501_yolo26s-default-and-manual-comments_feature-backend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(yolo): YOLO26s를 기본 비전 모델로 통일` |
| **커밋 번호 (SHA)** | `2db75015ba08f468e7c72b93ce728ee180d0d20d` |
| **짧은 SHA** | `2db7501` |
| **브랜치** | `feature/backend` |
| **부모 커밋** | `aa96658` |

## 2. 주 커밋 내용

- 비전 기본 스케일 **YOLO26n → YOLO26s** (seg: `yolo26s-seg.pt`, detect: `yolo26s.pt`)
- 전환 안내 문서 `docs/plan/YOLO26S_DEFAULT.md` 추가
- plan / guidance / AGENTS / RUN / models / training / .env.example 동기화
- 코드·설정 기본 경로 `config.yolo_model_path` 등 s 로 변경
- 사용자가 손댈 지점 `【수동】` 주석 보강 (config, nodes, segmentation, FE 등)

## 3. 상세 내용

### 3.1 배경 / 목적

마스크 품질과 학습·서빙 문서 일관성을 위해 기본 모델을 small 스케일로 통일.  
n 은 경량 옵션으로 경로 교체만 하면 되도록 문서에 남김.

### 3.2 주요 경로

- `docs/plan/YOLO26S_DEFAULT.md` (신규)
- `docs/plan/AI_MODEL_STRATEGY.md`, `LOGIC_STRUCTURE.md`, 기타 plan
- `backend/app/core/config.py`, `workflows/nodes.py`, `services/*`
- `training/yolo/train_*.py`, `export_onnx.py`
- `.env.example`, `models/README.md`

## 4. 커밋 관련 결과

- 로컬에 가중치 없으면 여전히 stub — **s 파일 배치 필요**
- origin `feature/backend` 푸시 예정

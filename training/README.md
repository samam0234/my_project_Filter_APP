# training — YOLO 학습 가이드

컷앤킵 **추론(`backend/`)** 과 분리된 학습 구역이다.  
이 문서는 **(1) 실행 전에 코드·데이터에서 맞춰야 할 것** → **(2) 실행 방법** 순서로 적는다.

| 구분 | 위치 | 역할 |
|------|------|------|
| **추론** | `backend/`, `models/` | 서비스 중 마스크·필터 |
| **학습** | **`training/`** (여기) | 데이터셋, train 스크립트, 산출물 |

**서비스 본선은 세그(seg).** detect 는 실험·검수용이다.

---

## 목차

1. [전체 그림](#1-전체-그림)
2. [실행 전 — 반드시 설정할 것](#2-실행-전--반드시-설정할-것) ← **여기부터 읽고 맞출 것**
3. [환경 준비 (CUDA / venv)](#3-환경-준비-cuda--venv)
4. [실행 방법](#4-실행-방법)
5. [학습 후 서비스에 넣기](#5-학습-후-서비스에-넣기)
6. [트러블슈팅](#6-트러블슈팅)
7. [하위 구조 · Git](#7-하위-구조--git)

---

## 1. 전체 그림

```text
[학습] training/
  데이터 + yaml names
       ↓ train_segment.py
  outputs/.../best.pt
       ↓ 수동 복사
[서빙] models/yolo26s-seg.pt + .env YOLO_MODEL_PATH
       ↓ backend 재시작
  사용자 프롬프트
       ↓ nodes.py 키워드 → target 리스트 (예: dog, person)
  segmentation.py
       ↓ YOLO 예측 후 names 라벨로 필터
  남긴 마스크만 effects 적용
```

**핵심:** 학습 yaml의 **클래스 이름(`names`)** 과  
백엔드 **프롬프트 키워드 → target 문자열** 이 **소문자로 같아야**  
“특정 개체만 인식/남기기”가 동작한다.

---

## 2. 실행 전 — 반드시 설정할 것

아래를 안 맞추면 학습은 돌아가도, 앱에서 **엉뚱한 객체만 잡히거나 전부 stub** 이 된다.

### 2.1 무엇을 “특정 개체”로 볼지 정하기

컷앤킵은 한 이미지에서 YOLO가 잡은 여러 인스턴스 중,  
**프롬프트가 가리키는 클래스만** 마스크로 남긴다.

| 단계 | 담당 | 하는 일 |
|------|------|---------|
| 프롬프트 분석 | `backend/app/workflows/nodes.py` | 자연어 → `target: ["dog", ...]` |
| 세그 + 필터 | `backend/app/services/segmentation.py` | YOLO 예측 → 라벨이 target 인 것만 마스크 합집합 |
| 학습 클래스 | `training/configs/*.yaml` 의 `names` | 모델이 출력하는 클래스 id ↔ 이름 |

예: 사용자가 `"강아지만 남기고 배경 블러"`  
→ 휴리스틱이 `target=["dog"]`  
→ YOLO 결과 중 라벨 `dog` 만 남김.

---

### 2.2 데이터셋 클래스 (`names`) — 학습 yaml

**파일:** `training/configs/dataset_seg.example.yaml` 을 복사해 사용

```powershell
cd d:\my_project\CutNKeep\training
copy configs\dataset_seg.example.yaml configs\dataset_seg.yaml
# 그다음 dataset_seg.yaml 편집
```

**수정 포인트**

```yaml
# 【수동】 데이터 루트 (training/ 기준 상대 또는 절대)
path: ../datasets/my_seg
train: images/train
val: images/val

# 【수동·중요】 클래스 id → 이름
# - id 순서가 라벨 .txt 첫 숫자와 1:1
# - 이름은 소문자 권장, 백엔드 keywords 의 label 과 동일
names:
  0: person
  1: dog
  2: cat
  3: car
  4: bag
```

| 규칙 | 설명 |
|------|------|
| id 변경 시 | 모든 `labels/**/*.txt` 의 class id 도 같이 다시 매핑 |
| 이름 변경 시 | `nodes.py` keywords 왼쪽 `label` 도 같은 문자열로 수정 |
| 새 클래스 | yaml `names` 추가 + 라벨 데이터 + keywords 행 추가 |

detect 실험 시: `dataset_detect.example.yaml` → `dataset_detect.yaml`  
**서비스 본선 마스크는 seg** — detect 전용 `best.pt` 를 세그 경로에 넣지 말 것.

---

### 2.3 이미지·라벨 폴더 구조

```text
training/datasets/my_seg/
  images/
    train/   *.jpg | *.png
    val/
  labels/
    train/   *.txt   ← 이미지와 stem 동일 (a.jpg ↔ a.txt)
    val/
```

#### 세그 (본선) — 폴리곤

한 줄 = 한 인스턴스:

```text
class_id x1 y1 x2 y2 x3 y3 ...   (좌표 0~1 정규화)
```

- **bbox만 있는 detect 라벨을 그대로 쓰면 안 됨** (세그 학습 깨짐)
- 폴리곤이 객체 외곽을 따라가야 마스크 품질이 나옴

#### detect (실험) — bbox

```text
class_id x_center y_center width height   (전부 0~1 정규화)
```

---

### 2.4 프롬프트 → 특정 개체 매핑 (백엔드 코드)

**파일:** `backend/app/workflows/nodes.py` → `parse_prompt_heuristic`

```python
# 【수동·하드코딩·중요】 한국어/영어 키워드 → YOLO 클래스 이름
keywords = [
    ("person", ["person", "사람", "인물"]),
    ("dog", ["dog", "강아지", "개"]),
    ("cat", ["cat", "고양이"]),
    ("car", ["car", "차", "자동차"]),
    ("bag", ["bag", "가방"]),
]
# 매칭 실패 시 기본:
# targets = ["person"]
```

**실행 전에 할 일**

1. 학습 `names` 에 있는 클래스마다 **왼쪽 label** 이 같은 철자인지 확인  
2. 사용자가 쓸 말(한/영)을 **오른쪽 리스트**에 넣기  
3. 새 개체 예: 병만 남기기  
   - yaml: `5: bottle`  
   - 데이터 라벨 id `5`  
   - keywords: `("bottle", ["bottle", "병", "보틀"])`  
4. 따옴표 안 문구는 키워드 없이 target 으로 씀: `"내 가방"` → target `["내 가방"]`  
   → 이때 YOLO names 에도 같은 문자열이 있어야 필터가 먹음 (보통 비권장, 표준 클래스명 권장)

기본 target 도 여기 수정:

```python
if not targets:
    targets = ["person"]   # 【수동】 기본 인식 대상
```

세그 쪽 기본값(프롬프트 누락 시):

**파일:** `backend/app/services/segmentation.py`

```python
targets = targets or ["person"]   # 【수동】 여기도 동일 정책으로 맞출 것
```

---

### 2.5 마스크 필터 정책 (어떤 bbox/인스턴스를 버릴지)

**파일:** `backend/app/services/segmentation.py` → `_predict_yolo`

동작 요약:

1. YOLO가 마스크·박스·클래스·conf 를 냄  
2. 각 인스턴스 라벨을 `names[class_id]` 로 읽고 **소문자** 비교  
3. `target` 목록에 없으면:  
   - conf 가 `min_confidence` **미만** → **버림**  
   - conf 가 높으면 완화 정책으로 남길 수 있음 (코드 주석의 현재 정책)  
4. 남는 마스크의 **합집합**이 최종 마스크

**설정 위치**

| 항목 | 어디 | 설명 |
|------|------|------|
| `min_confidence` | `backend/app/core/config.py` (Settings) | 낮은 conf 인스턴스 제거 기준 (기본 약 0.25) |
| target 엄격 매칭 | `segmentation.py` 필터 분기 | 엄격히 target 만 쓰려면 conf 완화 분기를 제거·수정 |
| `"all"` | target 에 `"all"` 포함 시 | 클래스 필터를 사실상 완화 |

**실행 전 체크리스트 (개체 인식)**

- [ ] `dataset_*.yaml` 의 `names` 확정  
- [ ] 라벨 id ↔ names 일치  
- [ ] `nodes.py` keywords 의 label = names 문자열 (소문자)  
- [ ] 기본 target (`person` 등) 이 데이터에 존재하는 클래스인지  
- [ ] 서비스에 넣을 가중치가 **seg** 인지 (detect only 금지)

---

### 2.6 경로·모델 파일 (서빙)

| 항목 | 파일 | 할 일 |
|------|------|--------|
| 가중치 경로 | 저장소 루트 `.env` | `YOLO_MODEL_PATH=models/yolo26s-seg.pt` |
| 가중치 배치 | `models/` | 학습 `best.pt` 를 **수동 복사** (자동 배포 없음) |
| Docker | `docker-compose.yml` | `./models` 마운트 — 호스트 `models/` 에 두면 컨테이너에서도 로드 |

사전학습 체크포인트를 쓸 때도 `models/` 또는 Ultralytics 캐시에 **seg** 가중치가 있어야 한다.  
파일 없으면 학습 스크립트/ultralytics 가 다운로드를 시도할 수 있음 (네트워크·용량 주의).

---

### 2.7 (선택) 효과·강도

개체 **인식**과 별개로, 남긴 마스크에 적용할 효과:

- `nodes.py` 의 effect 키워드 (`blur`, `블러`, `crop` …)  
- 기본 effect: `remove_bg`  
- 새 효과 추가 시: keywords + `effects.py` + 스키마 동시 수정  

이건 학습 필수 설정은 아니나, E2E 테스트 전에 맞추면 좋다.

---

## 3. 환경 준비 (CUDA / venv)

이 PC 기준: **CUDA Toolkit 13.3** 이미 설치  
(`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3`)

```powershell
cd d:\my_project\CutNKeep\training

# 1) venv + 경량 패키지 (torch 원격 대용량 자동 설치 안 함)
.\setup_cuda_env.ps1

# 2) 셸에 시스템 CUDA 연결
. .\env_cuda.ps1
nvcc --version    # 13.3 확인

# 3) venv 활성화
.\.venv\Scripts\Activate.ps1
```

### torch / ultralytics

학습 실행에는 **torch + ultralytics** 가 필요하다.  
스크립트는 **pytorch.org 2GB+ 휠을 勝手に 받지 않는다.**

```powershell
# 로컬 wheel 이 있을 때
.\setup_cuda_env.ps1 -TorchWheel "D:\path\to\torch-....whl"
# 또는 activate 후
pip install D:\path\to\torch-....whl
pip install ultralytics
```

검증:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import ultralytics; print(ultralytics.__version__)"
```

---

## 4. 실행 방법

### 4.0 사전 확인

```powershell
cd d:\my_project\CutNKeep\training
. .\env_cuda.ps1
.\.venv\Scripts\Activate.ps1

# yaml · 데이터 경로 존재
# configs\dataset_seg.yaml 의 path 가 실제 폴더를 가리키는지 확인
dir datasets\my_seg\images\train
dir datasets\my_seg\labels\train
```

---

### 4.1 세그 학습 (권장 · 서비스 본선)

```powershell
cd d:\my_project\CutNKeep\training
. .\env_cuda.ps1
.\.venv\Scripts\Activate.ps1

python yolo/train_segment.py `
  --model yolo26s-seg.pt `
  --data configs/dataset_seg.yaml `
  --epochs 100 `
  --imgsz 640 `
  --batch 8 `
  --name exp `
  --device 0
```

| 인자 | 의미 | 조정 |
|------|------|------|
| `--model` | 사전학습 체크포인트 | 로컬 경로 가능. n 쓰면 `yolo26n-seg.pt` 등 |
| `--data` | 데이터 yaml | **2.2 에서 만든 파일** |
| `--epochs` | 에폭 | 데이터 적을수록 과적합 주의 |
| `--imgsz` | 입력 한 변 | VRAM 부족 시 512 등 |
| `--batch` | 배치 | VRAM 에 맞게 4, 2 … |
| `--name` | run 이름 | 산출 폴더명 |
| `--device` | `0` / `cuda:0` / `cpu` | GPU 번호. 생략 시 자동 |

**산출물 (기본)**

```text
training/outputs/segment/<name>/weights/best.pt
training/outputs/segment/<name>/weights/last.pt
```

---

### 4.2 탐지 학습 (실험만)

```powershell
python yolo/train_detect.py `
  --model yolo26s.pt `
  --data configs/dataset_detect.yaml `
  --epochs 100 `
  --device 0
```

→ 현재 **backend Segmentor 는 seg 마스크 전제**.  
detect `best.pt` 만 `YOLO_MODEL_PATH` 에 넣지 말 것.

---

### 4.3 ONNX보내기 (선택)

```powershell
python yolo/export_onnx.py `
  --weights outputs/segment/exp/weights/best.pt `
  --out ../models/yolo26s-seg.onnx
```

`.env`:

```env
YOLO_MODEL_PATH=models/yolo26s-seg.onnx
```

---

### 4.4 구조 스모크 (저장소 루트)

```powershell
cd d:\my_project\CutNKeep
pytest tests/structure -q
```

---

## 5. 학습 후 서비스에 넣기

자동 배포 없음. **수동**.

```powershell
# 1) 가중치 복사 (PowerShell 예)
copy training\outputs\segment\exp\weights\best.pt models\yolo26s-seg.pt

# 2) .env
# YOLO_MODEL_PATH=models/yolo26s-seg.pt

# 3) backend 재시작
# 로컬: uvicorn ...
# Docker: docker compose -p cut_and_keep --env-file .env up -d backend
```

동작 확인:

1. API/UI 에 이미지 + 프롬프트 `"강아지만 남기고 배경 제거"`  
2. 로그에 세그 로드 / `parsed target` 에 `dog`  
3. 결과 마스크가 강아지 쪽인지 확인  
4. 실패 시 [2.4](#24-프롬프트--특정-개체-매핑-백엔드-코드)·[2.5](#25-마스크-필터-정책-어떤-bbox인스턴스를-버릴지) 다시 점검

---

## 6. 트러블슈팅

| 증상 | 원인 후보 | 조치 |
|------|-----------|------|
| `ultralytics` / `torch` import 오류 | 학습 venv 미활성·미설치 | activate + 로컬 wheel 로 torch 설치 |
| CUDA false | env_cuda 미실행, torch 가 CPU 빌드 | `. .\env_cuda.ps1`, CUDA용 torch 확인 |
| 학습 중 data yaml 오류 | path/train/val 틀림 | yaml `path` 와 실제 폴더 일치 |
| 마스크가 타원 stub | 가중치 없음·detect 모델·로드 실패 | seg `best.pt` 경로, 로그 확인 |
| 프롬프트와 다른 물체 | names ↔ keywords 불일치 | 소문자 label 통일 |
| 아무것도 안 남음 | target 필터 + conf | min_confidence, keywords, 데이터 클래스 확인 |
| OOM | batch/imgsz 과다 | `--batch 2` `--imgsz 512` |

---

## 7. 하위 구조 · Git

```text
training/
├── README.md                 ← 본 가이드
├── env_cuda.ps1              ← 시스템 CUDA 13.3 PATH 연결
├── setup_cuda_env.ps1        ← venv (torch 원격 자동 설치 없음)
├── requirements-training.txt
├── datasets/                 ← 이미지·라벨 (gitignore)
├── configs/
│   ├── dataset_seg.example.yaml
│   └── dataset_detect.example.yaml
├── yolo/
│   ├── train_segment.py      ← 본선
│   ├── train_detect.py
│   └── export_onnx.py
├── lora/                     ← Phase 2
└── outputs/                  ← best.pt 등 (gitignore)
```

### Git

- 데이터셋 대량 파일, `outputs/`, `*.pt` / `*.onnx` → **ignore**
- 스크립트·config 예시·README 만 추적

### 관련 문서

- `training/yolo/README.md` — 스크립트 요약  
- `models/README.md` — 가중치 배치  
- `docs/plan/YOLO26S_DEFAULT.md` — s 기본 스케일  
- `docs/plan/AI_MODEL_STRATEGY.md` — 비전·LLM 전략  
- `backend/app/workflows/nodes.py` — 프롬프트·target  
- `backend/app/services/segmentation.py` — 마스크 필터  

---

## 한 줄 요약

1. **실행 전:** 데이터 폴리곤 + yaml `names` + `nodes.py` keywords(+ 기본 target) + (선택) conf 정책을 **같은 클래스 문자열**로 맞춘다.  
2. **실행:** CUDA 셸 → venv → `train_segment.py` → `best.pt` → `models/` 복사 → `YOLO_MODEL_PATH` → backend 재시작.  
3. **특정 개체 인식:** 학습 클래스 이름 = 프롬프트 target 라벨 = 세그 필터 문자열 (소문자).

# training — 학습 전용 구역

컷앤킵 **추론 런타임(`backend/`)** 과 분리된  
**YOLO 탐지 · 세그멘테이션 · LoRA** 학습/실험 공간이다.

| 구분 | 위치 | 역할 |
|------|------|------|
| **추론** | `backend/`, `models/` (배포 가중치) | 서비스 중 마스크·필터 |
| **학습** | **`training/`** (여기) | 데이터셋, train 스크립트, run 산출물 |

## 하위 구조

```text
training/
├── README.md                 ← 본 문서
├── requirements-training.txt ← 학습용 의존성 (torch 등, 별도 venv 권장)
├── datasets/                 ← 원본/라벨 데이터 (gitignore 내용)
├── configs/                  ← 데이터 yaml, 하이퍼파라미터 예시
├── yolo/                     ← detect / segment 학습
│   ├── README.md
│   ├── train_detect.py
│   ├── train_segment.py
│   └── export_onnx.py
├── lora/                     ← 피드백 기반 LoRA (Phase 2)
│   ├── README.md
│   └── train_lora.py
└── outputs/                  ← runs, best.pt, 로그 (gitignore 내용)
```

## 권장 환경

- Python **3.11** 전용 venv (백엔드 venv와 **분리** 권장)
- GPU 있으면 CUDA 빌드 torch 사용

```powershell
cd d:\my_project\CutNKeep\training
python -m venv .venv
.\.venv\Scripts\activate
pip install -U pip
pip install -r requirements-training.txt
```

## 학습 → 서비스 적용 흐름

```text
1. datasets/ 에 YOLO 형식 데이터 준비
2. yolo/train_segment.py (또는 detect) 실행
3. outputs/.../weights/best.pt 생성
4. models/yolo26n-seg.pt 로 복사 (또는 원하는 이름)
5. .env 의 YOLO_MODEL_PATH 지정
6. backend 재시작 → segmentation.py 가 로드
```

ONNX 배포:

```powershell
python yolo/export_onnx.py --weights ../models/yolo26n-seg.pt --out ../models/yolo26n-seg.onnx
```

## 학습 전 검증

```powershell
# 저장소 루트 — training 스크립트·config 존재 확인
pytest tests/structure -q
```

## 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/plan/TESTING.md`
- `docs/guidance/llm-and-vision.md`
- `models/README.md`
- `scripts/README.md` (레거시 유틸 — 점진적으로 training/ 로 이전)

## Git 정책

- 데이터셋 이미지·라벨 대량 파일, `outputs/`, `*.pt` 는 **ignore**
- 스크립트·config·README 만 추적

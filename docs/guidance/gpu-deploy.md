# GPU 서버로 띄우기 (CUDA)

> 오버레이: [`docker-compose.gpu.yml`](../../docker-compose.gpu.yml) · 이미지: `backend/Dockerfile` (`TORCH_INDEX=cu128` · `LLM_LORA=1`)
> 근거: [`parser-compare-20261009.md`](../vaildates/parser-compare-20261009.md) — 283문장 LoRA 94.7% · Ollama 체인 85.2%

GPU 가 있으면 문장 해석을 **LoRA**(Qwen2.5-1.5B 어댑터)로 바꾸고, 세그(YOLO)도 GPU 로 돌린다.
CPU 이미지로는 LoRA 가 문장당 20초대라 쓸 수 없다. 그래서 GPU 서버에서만 켠다.

## 1. 준비

| 할 일 | 확인 |
|-------|------|
| NVIDIA 드라이버 | `nvidia-smi` |
| Linux: NVIDIA Container Toolkit · Windows: Docker Desktop(WSL2) GPU 지원 | `docker info` 의 Runtimes 에 `nvidia` |
| 모델 옮기기 (개발 PC 에서) | `python scripts/models_bundle.py pack --gpu` → 서버에서 `tar -xf` · `verify` (LoRA 어댑터 + 베이스 모델 약 3GB 포함, 전체 약 3.5GB) |

베이스 모델 폴더의 기본 위치는 `training/models/qwen2.5-1.5b-instruct` 다. 다른 곳에 두면 `.env` 의 `LORA_BASE_DIR` 로 알린다.

## 2. 띄우기

```powershell
# GPU 만
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
# HTTPS + GPU (공개 배포)
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.gpu.yml up -d --build
# 점검
python scripts/deploy_check.py server --gpu      # 베이스 모델 · 어댑터 · 컨테이너 CUDA · LLM_PROVIDER=lora
```

| 항목 | 기본 compose | + gpu |
|------|--------------|-------|
| backend 이미지 | `cut_and_keep-backend` (CPU torch) | `cut_and_keep-backend-gpu` (CUDA 12.8 torch + transformers · peft, 약 13GB) |
| 문장 해석 | Ollama(호스트) + 키워드 파서 체인 | **LoRA**, 실패하면 키워드 파서 (`GPU_LLM_PROVIDER` · `GPU_LLM_FALLBACK` 로 바꿀 수 있음) |
| 세그 (YOLO) | CPU | GPU (ultralytics 가 cuda 자동 선택) |
| SegFormer · LaMa (onnxruntime) | CPU | CPU (그대로) |

- 폴백을 `heuristic` 으로 둔 것은 의도다. Ollama(약 10GB)를 같은 GPU 에 또 올리면 12GB 카드에서 넘친다
- Ollama 를 폴백으로 쓰려면 `.env` 에 `GPU_LLM_FALLBACK=ollama` 를 둔다
- 되돌리기: `-f docker-compose.gpu.yml` 없이 다시 `up` 한다. CPU 이미지는 그대로 남아 있다

## 3. 로컬 리허설 결과 (2026-10-09, RTX 4070 SUPER 12GB · Docker Desktop WSL2)

- 컨테이너 안 `torch.cuda.is_available()` = True (CUDA 12.8). LoRA 는 cuda · bfloat16 으로 올라갔다
- **LoRA 해석: 문장당 평균 1.85초, 최대 2.14초**, GPU 메모리 3.1GB
  - 첫 호출은 Windows 폴더에서 모델을 읽느라 46초가 걸렸다
  - 같은 이미지를 CPU 로 돌리면 문장당 23초다
- HTTPS 로 사진 처리: 요청당 3.5~5초(해석 + 세그 + 효과)
  - 해석은 5건 모두 정답이었다: left · right 2명 · largest · center · 지우기
  - 백엔드가 뜬 뒤 첫 요청은 모델 로드로 56초가 걸렸다
- `deploy_check.py remote https://localhost --insecure`: 실패 0 · 경고 1(자체 서명)
- `server --gpu`: GPU 항목 모두 통과. 운영 값(APP_ENV · SMTP · DOMAIN)은 로컬이라 실패로 나왔다

## 4. CUDA 판 고르기 (`GPU_TORCH_INDEX`)

컨테이너는 **자기 CUDA 런타임**(PyTorch 휠 안에 들어 있다)을 쓰고, 호스트에서는 **NVIDIA 드라이버만** 빌린다.
그래서 호스트에 설치된 CUDA Toolkit 버전(예: 13.3)은 상관없다. 드라이버가 지원하는 CUDA(`nvidia-smi` 오른쪽 위)가 컨테이너 판 이상이면 된다.

| `GPU_TORCH_INDEX` | 컨테이너 CUDA | 필요한 드라이버 | 이미지 | 2026-10-10 측정 (RTX 4070 SUPER, 드라이버 591.86 = CUDA 13.1) |
|-------------------|---------------|-----------------|--------|---------------------------------------------------------------|
| `cu128` (기본) | 12.8 | 525 이상 (CUDA 12 마이너 호환) | 13.1GB | GPU 인식 · LoRA 정상 |
| `cu130` | 13.0 | 580 이상 | 9.7GB | GPU 인식 · LoRA 정상 |

- 속도 차이는 없었다. 문장당 0.5~1.9초로 측정마다 흔들렸고, 순서를 바꾸면 결과도 뒤집혔다(GPU 클럭 등 시스템 상태 영향)
- PyTorch 는 cu130 · cu132 휠을 내고, cu133 휠은 없다(2026-10). 그래서 Toolkit 13.3 에 맞춘 판은 없다
- **기본을 cu128 로 둔 이유**: 드라이버가 더 오래된 서버에서도 돈다. 서버 드라이버가 580 이상이면 `GPU_TORCH_INDEX=cu130` 으로 이미지를 줄여도 된다
- 바꾸면 다시 빌드한다(`up -d --build`). `python scripts/deploy_check.py server --gpu` 가 컨테이너의 CUDA 판을 보여 준다

## 주의

- **첫 요청이 느리다.** 모델 로드에 Linux 서버는 수 초~수십 초가 걸리고, Windows 바인드 마운트는 약 50초가 걸린다
  - 해석 제한 시간(`LLM_TIMEOUT_SECONDS`, 30초)을 넘기면 그 요청은 키워드 파서로 처리된다
  - 백엔드를 띄운 뒤 요청 하나를 미리 보내 두면 된다
- Windows Git Bash 의 `curl -F "prompt=한글"` 은 한글이 깨져서 간다. 시험할 때 해석이 이상하면 파이썬 `requests` 로 보내 본다
- 비로그인 처리 횟수 제한(`UPLOAD_RATE_GUEST_PER_MIN`)은 GPU 에서도 그대로다. 시험 중 429 가 나오면 정상이다

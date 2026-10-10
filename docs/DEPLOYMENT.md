# 배포 — 공개 서버에 올리는 순서

> 로컬 개발 실행은 [../RUN.md](../RUN.md) · [guidance/docker-run.md](./guidance/docker-run.md).
> 이 문서는 **공개 서버**에 올리는 순서만 모은다. 각 단계의 자세한 설명은 링크한 문서에 있다.

## 0. 고를 것

| 질문 | 선택 | 문서 |
|------|------|------|
| GPU 가 있나? | 없음 → 기본(CPU) · 있음 → `docker-compose.gpu.yml` 을 겹침 (문장 해석 LoRA · 세그 GPU) | [guidance/gpu-deploy.md](./guidance/gpu-deploy.md) |
| 서버 드라이버가 CUDA 13 을 지원하나? (`nvidia-smi` 오른쪽 위) | 12.x → `GPU_TORCH_INDEX=cu128`(기본) · 13.x(드라이버 580+) → `cu130` 도 가능 | gpu-deploy 4절 |
| 실패 사진을 모아 세그를 개선할까? | 기본 꺼짐. 켜면 `HARD_EXAMPLE_CONF=0.4` — 처리방침에 이미 적혀 있다(30일 보관) | [guidance/legal.md](./guidance/legal.md) · [guidance/learning-loop.md](./guidance/learning-loop.md) |

## 1. 서버 준비

1. 도메인을 사고 DNS **A 레코드**를 서버 공인 IP 로 잡는다. 방화벽에서 **80 · 443** 을 연다
2. Docker(+ Compose)를 설치한다. GPU 서버면 NVIDIA 드라이버와 NVIDIA Container Toolkit 도 설치한다
3. 저장소를 받는다(`git clone`). **모델은 git 에 없다** — 개발 PC 에서 묶어 옮긴다:

```bash
# 개발 PC
python scripts/models_bundle.py pack [--gpu]       # dist/models.tar + models.sha256.json (--gpu: LoRA 베이스 포함 약 3.5GB)
# 서버 (저장소 폴더)
tar -xf models.tar && python scripts/models_bundle.py verify models.sha256.json
```

LaMa 는 서버가 직접 받게 해도 된다(`MODEL_AUTO_DOWNLOAD=true` · `python scripts/fetch_models.py`).

## 2. 운영 `.env` 만들기

손으로 고치지 않는다. 운영 값 · 새 비밀 값 · 기동 전 점검을 한 번에 한다:

```bash
CNK_SMTP_PASSWORD='메일 계정 비밀번호' python scripts/make_prod_env.py \
    --domain cutnkeep.example.com --acme-email you@example.com \
    --smtp-host smtp.gmail.com --smtp-port 587 --smtp-user you@gmail.com \
    --operator-name 운영자 --operator-email privacy@example.com --console-admins admin
# → .env.production (git 제외) · "[preflight] 오류 0" 확인 → mv .env.production .env
```

자세히: [guidance/https-deploy.md](./guidance/https-deploy.md) 1절 · 메일 제공자별 값: [guidance/auth.md](./guidance/auth.md) 4절

## 3. 띄우기

```bash
# CPU 서버 (HTTPS)
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml up -d --build
# GPU 서버 (HTTPS + GPU)
docker compose -p cut_and_keep --env-file .env -f docker-compose.yml -f docker-compose.https.yml -f docker-compose.gpu.yml up -d --build
```

- Caddy 가 인증서를 자동으로 발급받는다. 확인: `docker compose -p cut_and_keep logs -f caddy` 에서 `certificate obtained`
- 첫 요청은 모델을 올리느라 느리다. 띄운 뒤 사진 하나를 미리 처리해 둔다
- 운영 콘솔(`console/`)은 Compose 에 없다 — 관리자 PC 에서 띄워 서버 API 에 붙인다 ([guidance/console-admin.md](./guidance/console-admin.md))

### 해석 모델 고르기를 쓰려면 (Ollama 서버)

작업실의 "해석 모델" 상자는 `LLM_PROVIDER=ollama` 일 때만 보인다. 서버의 Ollama 에 모델을 받아 두면 상자의 "미적용"이 풀린다:

```bash
ollama pull gemma4:e4b && ollama pull gemma4:12b && ollama pull qwen3.8:27b   # 27b 는 17GB — GPU 메모리가 모자라면 일부가 CPU 로 돌아 첫 호출이 3분 가깝다
```

GPU 서버(`docker-compose.gpu.yml`)는 LoRA 로 해석하므로 상자가 보이지 않는다. 큰 모델의 첫 호출을 위해 nginx 는 사진 요청을 300초까지 기다린다.

## 4. 점검

```bash
python scripts/deploy_check.py remote https://cutnkeep.example.com      # 밖에서 (아무 PC)
python scripts/deploy_check.py server [--gpu] --models-manifest models.sha256.json   # 서버 안
```

| 점검 | 보는 것 |
|------|---------|
| remote | 인증서 유효 · 만료 14일 이상, http→https, HSTS · CSP · X-Frame-Options · nosniff · 서버 버전 숨김, /health(서비스 DB MariaDB), 로그인 없는 요청 401, /docs 비노출, 다른 출처 CORS 거절, 약관 화면 |
| server | APP_ENV · SECRET_KEY · SMTP · DOMAIN · 운영자 정보, 모델 파일 · 체크섬, 최근 MariaDB 백업, Docker 서비스 상태, 개발 도구(adminer · mailpit) 경고, `--gpu`: 베이스 모델 · 어댑터 · 컨테이너 CUDA · LoRA |

실패가 있으면 종료 코드 1 이다. 그 밖의 수동 점검 항목은 [guidance/security.md](./guidance/security.md) 에 있다.

## 5. 운영 중

| 할 일 | 방법 |
|-------|------|
| 백업 확인 · 다른 곳으로 복사 | `data/mariaDB_backups/` (24시간마다 · 7일) — 복구 절차 [plan/DATABASE.md](./plan/DATABASE.md) |
| 학습 문장 검수 | 운영 콘솔 "학습 데이터" → 승인 문장이 쌓이면 `python scripts/retrain_lora.py` ([guidance/learning-loop.md](./guidance/learning-loop.md)) |
| 실패 사진으로 세그 개선 | `python scripts/seg_labeling.py export` → 라벨링 → `check` → `python scripts/retrain_yolo.py --extra` |
| 업데이트 | `git pull` → 같은 `up -d --build` → `deploy_check.py remote` |

## 로컬에서 미리 해 본 결과 (2026-10-09 ~ 10)

- HTTPS(localhost 자체 서명) + GPU(RTX 4070 SUPER) 로컬 리허설: remote 실패 0 · 경고 1(자체 서명)
- GPU 컨테이너: 문장 해석 LoRA 문장당 약 0.5~1.9초, 사진 처리 요청당 3.5~5초
- 실제 도메인 · 메일 서버로는 아직 돌려 보지 않았다

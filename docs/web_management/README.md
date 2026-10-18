# web_management — 배포 · 운영 관리

> 공개 서버를 올리기 **전 · 중 · 후**에 확인할 것과 포트 목록. 배포할 때 옆에 펴 두는 체크리스트 폴더.

배포 순서 전체는 [`../DEPLOYMENT.md`](../DEPLOYMENT.md), 지금 운영 구성과 서버 갱신 명령은 [`../HANDOVER.md`](../HANDOVER.md)가 정본이다. 이 폴더는 그 순서 사이사이에 확인하는 목록이다.

## 배포 흐름과 문서

```text
pre-deploy.md ──▶ docker-deploy.md ──▶ post-deploy.md
(배포 전 체크)      (Compose 배포 절차)     (배포 후 확인)
        ports-inventory.md (어느 포트가 어디에 열리나)
```

| 파일 | 내용 | 언제 |
|------|------|------|
| [pre-deploy.md](./pre-deploy.md) | 배포 전 체크 — 운영 `.env` · 비밀 값 · 처리방침 운영자 정보 · 모델 · 백업 · 법률 검토 | 배포하기 전 |
| [docker-deploy.md](./docker-deploy.md) | Compose 배포 절차 | 배포할 때 |
| [post-deploy.md](./post-deploy.md) | 배포 후 확인 | 배포 직후 |
| [ports-inventory.md](./ports-inventory.md) | 포트 인벤토리 — 로컬 · Docker · 공개 | 포트를 열거나 충돌이 날 때 |

## 배포 뒤 꼭 보는 것

| 확인 | 기준 |
|------|------|
| `python scripts/deploy_check.py remote https://168-110-17-193.sslip.io` | **실패 0 · 경고 0** |
| 서버와 Cloudflare Worker의 화면 번들 이름(`assets/index-*.js`) | 같아야 한다 |
| `/health` (서버 · Worker 주소 모두) | 200 |
| `/api/v1/llm/models` | `enabled: true` · `reachable: true` (PC Ollama 터널) |
| 공개 포트 | 22 · 80 · 443뿐 |
| 서버 갱신 방식 | 서비스를 지정해 `up -d --build backend frontend caddy ollama-bridge` — 전체 `up`은 Adminer까지 띄운다 |

## 기록 규칙

- 배포할 때마다 무엇을 올렸는지(커밋 · 서비스 · 결과)를 [`../DEPLOYMENT.md`](../DEPLOYMENT.md)의 배포 기록이나 커밋 기록([`../branchs/commits/`](../branchs/README.md))에 남긴다.
- 실패한 배포 · 롤백도 남긴다. 원인이 인프라 문제면 [`../repeater/`](../repeater/README.md)에도.
- 비밀 값은 적지 않는다. 키 이름만 적는다.

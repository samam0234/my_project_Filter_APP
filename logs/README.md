# logs — 학습 · 스크립트 로그

> `training/` · `scripts/`를 돌린 기록을 남기는 곳. 백엔드 앱 로그는 여기가 아니라 [`backend/logs/`](../backend/logs/README.md)에 `app_YYYY-MM-DD.log`로 쌓인다.

| 로그 | 위치 |
|------|------|
| 백엔드 앱 (요청 · 기동 · 메일 · 콘솔 작업) | `backend/logs/` — 자동, 14일 보관 |
| 학습 · 재학습 · 실험 · 배포 점검 | **여기** — 콘솔 출력이 기본이고, 남기고 싶을 때 리다이렉트 |
| 브라우저 확인 기록 (`scripts/experiments/ui_check.py`) | `logs/ui_check/` — 스크린샷 등, Git 제외 |

## 남기는 법

```powershell
# PowerShell
python training/yolo/train_segment.py *> logs/train_segment_$(Get-Date -f yyMMdd_HHmm).log
python scripts/retrain_lora.py *> logs/retrain_lora_$(Get-Date -f yyMMdd_HHmm).log
```

```bash
# Git Bash · Linux
python scripts/deploy_check.py remote https://168-110-17-193.sslip.io 2>&1 | tee logs/deploy_check_$(date +%y%m%d_%H%M).log
```

파일 이름은 `<무엇>_<YYMMDD_HHMM>.log`로 맞추면 시간 순으로 찾기 쉽다.

## Git

- 로그 파일 내용은 **ignore**. 폴더 유지용 `.gitkeep`과 이 README만 추적한다.
- 결과를 문서로 남길 수치는 로그가 아니라 [`docs/vaildates/`](../docs/vaildates/README.md)에 정리한다.

## 장애를 만났을 때

```powershell
# Docker 백엔드 로그
docker compose -p cut_and_keep logs -f backend

# 로컬 백엔드 파일 로그
Get-Content backend/logs/app_$(Get-Date -f yyyy-MM-dd).log -Wait -Encoding utf8
```

원인과 해결은 기록해 둔다 — 작업 · 실행 디버깅은 [`docs/find_debug/`](../docs/find_debug/README.md), 서버 연결 · 인프라 장애는 [`docs/repeater/`](../docs/repeater/README.md).

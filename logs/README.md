# logs — 학습·스크립트 로그

`training/`·`scripts/` 실행 결과 로그를 남기는 디렉터리이다.
백엔드 앱 로그는 [`backend/logs/`](../backend/logs/README.md) 에 `app_YYYY-MM-DD.log` 로 쌓인다.

## 현재

- 학습·스크립트는 콘솔 출력이 기본. 남기고 싶으면 리다이렉트로 저장한다.

```powershell
python training/yolo/train_segment.py *> logs/train_segment_$(Get-Date -f yyMMdd_HHmm).log
```

## Git

- 로그 파일 내용은 **ignore**
- 폴더 유지용 `.gitkeep` 만 추적

## 팁

```powershell
# Docker 백엔드 로그
docker compose -p cut_and_keep logs -f backend

# 로컬 백엔드 파일 로그
Get-Content backend/logs/app_$(Get-Date -f yyyy-MM-dd).log -Wait -Encoding utf8
```

장애 기록은 `docs/find_debug/`, `docs/repeater/` 에 정리하는 것을 권장한다.

# logs — 런타임 로그

애플리케이션·스크립트가 남기는 **로그 파일**용 디렉터리이다.

## 현재

- 백엔드는 기본적으로 **stderr / loguru 콘솔** 출력.
- 파일 로그를 쓰도록 확장할 때 이 경로를 사용하면 된다.
- Docker Compose 는 `./logs` → `/app/logs` 마운트.

## Git

- 로그 파일 내용은 **ignore**
- 폴더 유지용 `.gitkeep` 만 추적

## 팁

```powershell
# Docker 백엔드 로그
docker compose -p cut_and_keep logs -f backend

# 로컬 uvicorn 은 터미널 출력 확인
```

장애 기록은 `docs/find_debug/`, `docs/repeater/` 에 정리하는 것을 권장한다.

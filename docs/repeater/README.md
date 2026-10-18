# repeater — 다시 날 수 있는 인프라 장애와 해결

> 연결 실패 · 포트 충돌 · DB 끊김처럼 **또 만날 수 있는** 서버 · 인프라 문제를, 증상으로 찾아 바로 고칠 수 있게 모은다.

날짜별 작업 디버깅은 [`../find_debug/`](../find_debug/README.md)에 둔다. 이 폴더는 "같은 증상이 또 나면 이렇게"에 집중한다.

## 증상으로 찾기

| 증상 | 문서 |
|------|------|
| 모든 `/api`가 **502**인데 백엔드 컨테이너는 떠 있다 (재배포 · `.env` 변경 직후) | [nginx-backend-502.md](./nginx-backend-502.md) — nginx가 백엔드의 옛 IP를 붙들고 있었다. `resolver`로 해결 |
| 로컬에서 가입했는데 **인증 메일이 안 온다** | [local-mail-not-sent.md](./local-mail-not-sent.md) — SMTP 미설정 개발 모드에서는 메일이 로그에만 남는다 |
| backend가 **MariaDB에 연결하지 못한다** · 호스트 주소를 뭘로 써야 할지 모르겠다 | [mariadb-connection.md](./mariadb-connection.md) — `172.18.0.x`는 Docker 안쪽, SSL · GSS 없이 비밀번호만 |
| Redis **6379 포트 충돌** (`port is already allocated`) | [docker-redis-port.md](./docker-redis-port.md) — 다른 스택의 Redis가 6379를 점유. 이 스택은 호스트 6380을 쓴다 |
| `ImportError: engine from app.db.session` · 컨테이너가 Restarting | [backend-import-engine.md](./backend-import-engine.md) — `app/db/__init__.py`가 없는 이름 `engine`을 import했다. `get_engine` · `SessionLocal` · `get_db` · `init_db`만 내보낸다 |
| Docker Images 목록에 **예전 프로젝트 이미지가 섞여** 보인다 | [image-list-mixed-projects.md](./image-list-mixed-projects.md) — 이미지 저장소는 Docker 전역이라 섞여 보인다. 이 프로젝트만 보려면 `docker compose -p cut_and_keep images` |

## 빠른 진단 순서

1. **서버 직접 주소**(`https://168-110-17-193.sslip.io/health`)가 되는가?
   - 안 되면 서버 쪽 — 컨테이너 상태 · 백엔드 로그 · nginx 502 확인
   - 되는데 Worker 주소만 안 되면 Worker 쪽 — `EDGE_SECRET` 불일치 · 100초 제한(524)
2. `docker compose -p cut_and_keep ps` — 모든 서비스가 Up인가, MariaDB가 healthy인가
3. `docker compose -p cut_and_keep logs --since 10m backend` — 기동 점검(preflight) 실패 · DB 연결 · 모델 없음
4. AI 해석이 키워드 파서로만 동작하면 `/api/v1/llm/models`의 `reachable` — PC Ollama 터널이 끊겼는지

## 이슈 작성 템플릿

```markdown
# <한 줄 증상>

1. 환경 — local / docker / 운영 서버, 관련 버전
2. 증상 — 사용자가 본 것, 로그 원문
3. 원인 — 왜 그랬나 (확인한 근거)
4. 해결 — 한 일, 바꾼 파일 · 설정
5. 검증 명령 — 고쳐졌음을 확인한 명령과 결과
6. 재발 방지 — 문서 · 코드 · 점검 스크립트에 넣은 것
```

- 비밀 값(비밀번호 · 키 · 토큰)은 로그를 붙일 때도 지운다.
- 운영 서버에서 겪은 함정의 요약은 [`../HANDOVER.md` 7절](../HANDOVER.md)에도 한 줄로 남긴다.

# repeater — 서버 연결 · 인프라 장애 기록

연결 실패, 포트 충돌, DB 끊김 등 **재발 가능한 인프라 이슈**와 해결책을 모은다.

## 목록

| 파일 | 주제 |
|------|------|
| [docker-redis-port.md](./docker-redis-port.md) | Redis 6379 충돌 |
| [mariadb-connection.md](./mariadb-connection.md) | backend ↔ MariaDB |
| [backend-import-engine.md](./backend-import-engine.md) | db package import |
| [image-list-mixed-projects.md](./image-list-mixed-projects.md) | Images 혼재 설명 |

## 템플릿 (이슈 작성 시)

1. 환경 (local/docker)
2. 증상
3. 원인
4. 해결
5. 검증 명령

# Ports Inventory

현재 기준: [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

| 포트 | 용도 | 비고 |
|------|------|------|
| 80 | cut_and_keep frontend (nginx) | Docker |
| 8000 | backend API | Docker / local |
| 5173 | frontend dev | local Vite |
| 5174 | console dev | local Vite · Compose 없음 |
| **3309** (예) | MariaDB **호스트** 발행 | `.env` `MARIADB_PORT` — 컨테이너 내부는 3306 |
| 3306 | (호스트 기본 매핑 시) MariaDB | 충돌 시 3309 등 사용 |
| 6379 | 타 프로젝트 Redis 등 | 점유 시 cut_and_keep 은 6380 |
| **6380** | cut_and_keep Redis 호스트 맵 | → 컨테이너 6379 |
| **8081** | **Adminer** | Server=`mariadb` |

## 주의

- `172.18.0.x` 는 Docker 브리지 게이트웨이 — DBeaver Host 로 쓰지 말 것
- 구 스택 `cutnkeep` 과 포트/이름 중복 금지

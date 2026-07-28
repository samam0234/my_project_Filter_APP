# Training: Docker Compose Project Isolation

## 학습 내용

- `-p cut_and_keep` → 컨테이너·네트워크·볼륨 prefix (`cut_and_keep_*`)
- 네트워크 이름: `cut_and_keep_net`
- Images 목록은 Docker Engine **전역** → UI에 예전 이미지 혼재 가능
- 포트 바인딩은 호스트 단일 자원 → 프로젝트 간 충돌
- **구 이름 `cutnkeep` 스택과 동시 기동 금지**

## 현재 포트 (요약)

| 호스트 | 서비스 |
|--------|--------|
| 80 | frontend nginx |
| 8000 | backend |
| MARIADB_PORT (예 3309) | MariaDB |
| 6380 | Redis |
| 8081 | Adminer |

→ [`docs/plan/CURRENT_STACK.md`](../plan/CURRENT_STACK.md)

## 실습

1. `docker compose -p cut_and_keep ps`
2. `docker images` 와 비교해 전역성 확인
3. `docker compose -p cut_and_keep down` 후 다른 스택 영향 없는지 확인

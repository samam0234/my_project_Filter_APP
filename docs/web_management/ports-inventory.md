# Ports Inventory

| 포트 | 용도 | 비고 |
|------|------|------|
| 80 | cut_and_keep frontend (nginx) | Docker |
| 8000 | backend API | Docker/local |
| 5173 | frontend dev | local |
| 5174 | **console dev** | local |
| 3306 | MariaDB | 충돌 주의 |
| 6379 | 타 프로젝트 Redis 등 | 점유 시 cut_and_keep은 6380 |
| 6380 | cut_and_keep Redis host map | |

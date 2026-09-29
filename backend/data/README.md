# backend/data — 서비스 런타임 데이터

백엔드가 요청을 처리하면서 만들고, **서비스 안에서만** 쓰는 데이터이다.
학습 재료(feedback·pseudo_labels)는 여기가 아니라 루트 [`data/`](../../data/README.md) 에 둔다.

| 경로 | 용도 | 수명 |
|------|------|------|
| `uploads/{job_id}/` | before/after 이미지 | `FILE_RETENTION_HOURS` 뒤 `scripts/cleanup.py` 가 삭제 |
| `cutnkeep.db` | SQLite (`jobs`·`feedbacks`·`batch_jobs`, 로컬 `DB_DIALECT=sqlite`) | 영구 |

## 설정 (backend/ 기준 상대 경로)

```env
UPLOAD_DIR=data/uploads
SQLITE_PATH=data/cutnkeep.db
FILE_RETENTION_HOURS=24
```

## Docker

Compose 가 `./backend/data` → `/app/data` 로 마운트한다.
Docker backend 는 `DB_DIALECT=mariadb` 라서 SQLite 파일은 쓰지 않는다.

## Git

내용은 전부 ignore. `uploads/.gitkeep` 과 이 README 만 추적.

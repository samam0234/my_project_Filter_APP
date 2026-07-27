# data — 런타임 데이터

업로드 결과, 피드백 덤프, DB 파일 등이 쌓이는 **데이터 루트**이다.  
기본 설정은 프로젝트 루트 기준 상대 경로 (`core/config.py`).

## 하위 디렉터리

| 경로 | 용도 | Git |
|------|------|-----|
| `uploads/` | Job 별 before/after 이미지 | 내용 ignore (`.gitkeep` 만 추적) |
| `feedback/` | 실패/피드백 사이드카 JSON·이미지 | 내용 ignore |
| `pseudo_labels/` | Phase 2 의사 라벨 | 내용 ignore |
| `cutnkeep.db` | SQLite (로컬 `DB_DIALECT=sqlite`) | ignore |

## 설정

```env
UPLOAD_DIR=data/uploads
FEEDBACK_DIR=data/feedback
PSEUDO_LABEL_DIR=data/pseudo_labels
SQLITE_PATH=data/cutnkeep.db
FILE_RETENTION_HOURS=24
```

Docker Compose 는 `./data` 를 컨테이너 `/app/data` 에 마운트한다.

## 정책

- 일반 업로드는 **영구 보관하지 않음** (보관 시간 후 cleanup 대상).
- 피드백 실패 케이스는 학습 루프용으로 별도 보관 가능.
- **비밀·개인 식별 원본**을 장기 두지 않도록 운영 정책을 정할 것.

## 관련 문서

- `docs/plan/DATABASE.md`
- `scripts/cleanup.py`

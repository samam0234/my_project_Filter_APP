# Backend Layers

```
routers/        HTTP, Depends(get_db), response mapping
schemas/        Pydantic request/response DTO
services/       domain + OpenCV pipeline helpers
workflows/      LangGraph orchestration
repositories/   SQL CRUD only
models/         SQLAlchemy ORM tables
db/             engine, session, init_db
```

## 의존 방향 (허용)

```
routers → services/workflows → repositories → models
routers → schemas
services ↛ routers
repositories ↛ services
```

## 책임 분리

| 계층 | 해도 됨 | 하면 안 됨 |
|------|---------|------------|
| Router | 검증, DB 세션 주입 | raw SQL, OpenCV |
| Schema | DTO 직렬화 | DB 커밋 |
| Service | 비즈니스, 파일 I/O | HTTP status 직접 처리(가능하면 예외) |
| Repository | commit/query | 프롬프트 파싱, 마스크 연산 |

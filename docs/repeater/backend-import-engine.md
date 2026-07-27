# ImportError: engine from app.db.session

## 증상
Uvicorn 기동 실패, 컨테이너 Restarting

## 원인
`app/db/__init__.py` 가 없는 이름 `engine` import

## 해결
`get_engine`, `SessionLocal`, `get_db`, `init_db` 만 export

## 검증
```bash
docker compose -p cut_and_keep logs backend --tail 20
# Application startup complete
```

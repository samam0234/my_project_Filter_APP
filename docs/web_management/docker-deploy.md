# Docker Deploy Procedure

```bash
git checkout develop
git pull
cp .env.example .env   # 운영 값 수정
docker compose -p cut_and_keep up --build -d
docker compose -p cut_and_keep ps
curl http://localhost:8000/health
```

롤백:

```bash
docker compose -p cut_and_keep down
# 이전 이미지 태그 사용 시 docker tag / compose image pin 필요 (추후 고도화)
```

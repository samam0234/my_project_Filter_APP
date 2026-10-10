# Redis host port conflict

## 환경
Docker Desktop, Windows, 다른 Compose 스택 병행

## 증상
`Bind ... 6379 failed: port is already allocated`

## 원인
`minchodan-redis` 등이 6379 점유

## 해결
`6380:6379` 매핑. 앱 간 통신은 `redis:6379` 유지.

## 검증
```bash
docker compose -p cut_and_keep ps
# redis Up, 0.0.0.0:6380->6379/tcp
```

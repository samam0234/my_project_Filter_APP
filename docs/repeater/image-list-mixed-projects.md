# Docker Images 목록에 예전 프로젝트가 섞여 보임

## 설명
Docker Engine 이미지 저장소는 **전역**이다. Compose 프로젝트 이름은 컨테이너/네트워크/볼륨을 가른다.

## 분리 방법

```bash
# 이 프로젝트만
docker compose -p cut_and_keep images
docker compose -p cut_and_keep down

# cut_and_keep 이미지만 삭제
docker rmi cut_and_keep-backend cut_and_keep-frontend

# 주의: system prune -a 는 다른 프로젝트 미사용 이미지도 삭제
```

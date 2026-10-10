# fix/mariadb-client-skip-ssl → develop 병합 (no-ff) / `3c81ab3bc35c8c1615895f28628794d7b1faebe0`

> 브랜치: `develop`  
> 작성일: `2026-10-04 03:21`  
> 작성자: `agent`  
> 파일명: `261004_0321_3c81ab3_merge-mariadb-client-skip-ssl_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: fix/mariadb-client-skip-ssl into develop (no-ff)` |
| **커밋 번호 (SHA)** | `3c81ab3bc35c8c1615895f28628794d7b1faebe0` |
| **짧은 SHA** | `3c81ab3` |
| **브랜치** | `develop` |
| **부모 커밋** | `dd3f5cc` (develop), `a309663` (fix tip) |

## 2. 주 커밋 내용

- 컨테이너 안 mariadb 클라이언트 명령에 `--skip-ssl` 추가 (`6bf771e`)

## 3. 상세 내용

### 3.1 배경 / 목적
"MariaDB 연결 안 됨" 진단 중 발견한 문서 명령 오류 수정. 원인 자체는 Docker Desktop 꺼짐.

### 3.2 변경 범위
- `docker/mariadb/README.md`, `docs/repeater/mariadb-connection.md`
- 기록: `261004_0320_6bf771e_mariadb-client-skip-ssl_fix-mariadb-client-skip-ssl.md`

### 3.3 기술 포인트
- `git merge --no-ff`, 충돌 없음

### 3.4 의도적으로 하지 않은 것
- 원격 push, main 병합

## 4. 커밋 관련 결과

### 4.1 동작 결과
- 문서만 변경

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 전체 스택(backend·frontend 컨테이너) 기동 확인

### 4.4 관련 문서
- `docker/mariadb/README.md`

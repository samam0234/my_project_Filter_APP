# 컨테이너 안 mariadb 클라이언트 명령에 --skip-ssl 추가 / `6bf771e23c8820c594d48b990ed17e1aaec838eb`

> 브랜치: `fix/mariadb-client-skip-ssl`  
> 작성일: `2026-10-04 03:20`  
> 작성자: `agent`  
> 파일명: `261004_0320_6bf771e_mariadb-client-skip-ssl_fix-mariadb-client-skip-ssl.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(docker): 컨테이너 안 mariadb 클라이언트 명령에 --skip-ssl 추가` |
| **커밋 번호 (SHA)** | `6bf771e23c8820c594d48b990ed17e1aaec838eb` |
| **짧은 SHA** | `6bf771e` |
| **브랜치** | `fix/mariadb-client-skip-ssl` |
| **부모 커밋** | `dd3f5cc` (develop) |

## 2. 주 커밋 내용

- `docker/mariadb/README.md`: 덤프·복원·접속 확인 명령에 `--skip-ssl`, 안내 박스
- `docs/repeater/mariadb-connection.md`: 실패 시 체크 6번

## 3. 상세 내용

### 3.1 배경 / 목적

"MariaDB 연결이 안 된다"는 요청을 진단하던 중, 원인은 Docker Desktop 이 꺼져 있던 것이었다(컨테이너·포트 없음).
Docker 를 켜고 MariaDB 를 올린 뒤 컨테이너 안에서 `docker exec … mariadb -u…` 를 실행하자
`ERROR 2026 (HY000): TLS/SSL error: SSL is required, but the server does not support it` 로 실패했다.
서버는 `--skip-ssl` 인데 mariadb 11 클라이언트 기본값은 SSL 필수이기 때문. 직전 커밋(`ecc478d`)에서
내가 문서에 넣은 덤프·복원 명령도 같은 문제였다.

### 3.2 변경 범위

- 수정: `docker/mariadb/README.md`, `docs/repeater/mariadb-connection.md`

### 3.3 기술 포인트

- 호스트(3309)에서 PyMySQL 접속은 이미 정상 — 컨테이너 내부 클라이언트만 해당
- 실제 컨테이너(`mariadb:11.8.9`)에서 `--skip-ssl` 로 `admin@%` · DB `cutnkeep` · utf8mb4 확인

### 3.4 의도적으로 하지 않은 것

- 서버의 `--skip-ssl` 제거 (로컬 개발 정책 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] Docker Desktop 기동 → `up -d mariadb` → healthy, 포트 3309 LISTEN, `data/mariaDB_datas` 에 DB 파일 생성
- [x] 호스트 → 3309 접속 성공, 컨테이너 내부 `--skip-ssl` 접속 성공
- 이 PC 에는 기존 컨테이너·볼륨이 없어 이전할 데이터는 없었음

### 4.2 부작용 / 리스크

- 없음 (문서만)

### 4.3 후속 작업

- backend·frontend 컨테이너까지 올리는 전체 스택 기동 확인 (`up -d --build`)

### 4.4 관련 문서

- `docker/mariadb/README.md`

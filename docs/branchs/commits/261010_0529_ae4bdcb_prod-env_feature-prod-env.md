# 운영 .env 만들기 도구 — 운영 값 · 새 비밀 값 · 기동 전 점검을 한 번에 / `ae4bdcbacb4ea2715d4d96973884a7ecb5489463`

> 브랜치: `feature/prod-env`  
> 작성일: `2026-10-10 05:29`  
> 작성자: `agent`  
> 파일명: `261010_0529_ae4bdcb_prod-env_feature-prod-env.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): 운영 .env 만들기 도구 — 운영 값 · 새 비밀 값 · 기동 전 점검을 한 번에` |
| **커밋 번호 (SHA)** | `ae4bdcbacb4ea2715d4d96973884a7ecb5489463` |
| **짧은 SHA** | `ae4bdcb` |
| **브랜치** | `feature/prod-env` |
| **부모 커밋** | `132145c` |

## 2. 주 커밋 내용

- `scripts/make_prod_env.py` (운영 .env 만들기 · 점검)
- `deploy_check.py server --env-file`

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "실서버 검증이 없음" — 서버가 없으므로, 서버에서 바로 쓸 운영 설정을 실수 없이 만드는 도구.

### 3.2 변경 범위
- 추가: `scripts/make_prod_env.py`
- 수정: `scripts/deploy_check.py`, `tests/unit/test_deploy_tools.py`, `.gitignore`, `docs/guidance/https-deploy.md`, `scripts/README.md`

### 3.3 기술 포인트
- 비밀번호를 명령줄에 쓰지 않음(환경 변수), 기존 파일 덮어쓰기 금지(비밀 값 보호)
- 만든 직후 기존 preflight 로 검증

### 3.4 의도적으로 하지 않은 것
- 이 PC 의 .env 를 바꾸기 (개발 환경 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 생성 파일 preflight 오류 0 · 경고 0, 테스트 통과

### 4.2 부작용 / 리스크
- MariaDB 비밀번호는 새 DB 에서만 적용 (문서화)

### 4.3 후속 작업
- 실서버에서 생성 → deploy_check

### 4.4 관련 문서
- `docs/guidance/https-deploy.md`

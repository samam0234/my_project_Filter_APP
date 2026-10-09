# 라우터 밖 DB 세션도 테스트 DB 로 묶기, CI 설치 충돌 · 의존성 점검 추가 / `d6236a33dfbbfcee2fe24aaf99b301bc630921ba`

> 브랜치: `feature/ci-isolation`  
> 작성일: `2026-10-10 06:03`  
> 작성자: `agent`  
> 파일명: `261010_0603_d6236a3_ci-isolation_feature-ci-isolation.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(test): 라우터 밖 DB 세션도 테스트 DB 로 묶기, CI 설치 충돌 · 의존성 점검 추가` |
| **커밋 번호 (SHA)** | `d6236a33dfbbfcee2fe24aaf99b301bc630921ba` |
| **짧은 SHA** | `d6236a3` |
| **브랜치** | `feature/ci-isolation` |
| **부모 커밋** | `d45fae2` |

## 2. 주 커밋 내용

- 테스트 DB 격리 강화 (`tests/unit/conftest.py`)
- CI 설치 충돌 수정 · pip-audit · 주간 실행

## 3. 상세 내용

### 3.1 배경 / 목적
의존성을 올린 뒤 CI 와 같은 깨끗한 환경에서 확인하다가, 테스트가 실제 DB 를 여는 경로와 CI 설치 충돌을 발견.

### 3.2 변경 범위
- 수정: `tests/unit/conftest.py`, `tests/unit/test_deploy_tools.py`, `tests/requirements-test.txt`, `.github/workflows/ci.yml`

### 3.3 기술 포인트
- 엔진 싱글톤을 바꿔 두면 직접 세션을 여는 모든 경로가 테스트 DB 로 감
- 실제 DB 파일 수정 시각 · 배치 행 0건으로 오염 없음 확인

### 3.4 의도적으로 하지 않은 것
- 코드 쪽 세션 주입 구조 변경 (테스트 고정 장치로 충분)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] CI 조건 전체 통과(1 건너뜀), 학습 venv 451 통과, pip-audit 0건

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- push 후 실제 Actions 결과 확인

### 4.4 관련 문서
- `docs/plan/TESTING.md`

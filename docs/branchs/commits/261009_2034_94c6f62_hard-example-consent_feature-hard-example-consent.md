# 처리 실패 회원 사진에 보관 기간 · 계정 삭제 시 삭제, 개인정보 처리방침을 실제 동작에 맞춤 / `94c6f626894c4ba1d5e631824bf288291122ee01`

> 브랜치: `feature/hard-example-consent`  
> 작성일: `2026-10-09 20:34`  
> 작성자: `agent`  
> 파일명: `261009_2034_94c6f62_hard-example-consent_feature-hard-example-consent.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(privacy): 처리 실패 회원 사진에 보관 기간 · 계정 삭제 시 삭제, 개인정보 처리방침을 실제 동작에 맞춤` |
| **커밋 번호 (SHA)** | `94c6f626894c4ba1d5e631824bf288291122ee01` |
| **짧은 SHA** | `94c6f62` |
| **브랜치** | `feature/hard-example-consent` |
| **부모 커밋** | `98fad0e` |

## 2. 주 커밋 내용

- `services/feedback_images.py` (보관 기간 정리 · 계정 삭제 시 정리)
- 개인정보 처리방침 화면 · legal.md 개정

## 3. 상세 내용

### 3.1 배경 / 목적
"실패 사진 수집(HARD_EXAMPLE_CONF) 동의 문구" 작업 중, 이미 실패 사진이 방침과 다르게 무기한 남는 것을 발견해 동작부터 고침.

### 3.2 변경 범위
- 추가: `backend/app/services/feedback_images.py`, `tests/unit/test_feedback_images.py`
- 수정: `config.py`, `maintenance.py`, `routers/console.py`, `user_admin.py`, 프론트 `legal.ts` · `PrivacyPage.tsx` · `vite-env.d.ts` · Dockerfile, `docker-compose.yml`, `.env.example`, legal · learning-loop · FEATURES, `test_console_users.py`

### 3.3 기술 포인트
- 테스트가 실제 학습 DB 를 열지 않도록 회원 삭제 경로는 호출 측 세션을 넘겨받음

### 3.4 의도적으로 하지 않은 것
- HARD_EXAMPLE_CONF 켜기 (운영자 결정), 보관 일수 정책 결정 (기본 30일 — 운영자가 바꿀 수 있음)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 전체 · 프론트 54 · 타입 검사 통과

### 4.2 부작용 / 리스크
- 기존 피드백 사진 중 30일 지난 것은 다음 정리 때 지워짐 (세그 라벨링에 쓰려면 그 전에 seg_labeling export)

### 4.3 후속 작업
- 운영자가 보관 일수 확정 · 법률 검토

### 4.4 관련 문서
- `docs/guidance/legal.md`

# 개인정보 처리방침 · 이용약관

사용자 앱에 두 화면이 있다 — `/privacy`(개인정보 처리방침) · `/terms`(이용약관). 푸터와 회원가입 화면에서 연결된다.

> **법률 검토 전 초안이다.** 실제 동작(보관 기간 · 수집 항목 · 외부 전송)에 맞춰 썼지만, 공개 서비스라면 공개 전에 전문가 검토를 받는다.

## 공개 전에 채울 것 (필수)

`.env` 에 넣고 frontend 를 다시 빌드한다 (빌드 때 화면에 박힌다):

```env
OPERATOR_NAME=운영자(사업자) 이름
OPERATOR_EMAIL=privacy@example.com     # 개인정보 문의 · 계정 삭제 요청 받는 주소
POLICY_DATE=2026-10-09                 # 시행일
```

비어 있으면 화면에 "(설정 필요)"가 보인다. 로컬 Vite 로 띄울 때는 `frontend/.env` 에 `VITE_OPERATOR_NAME` 등으로 넣는다.

## 문서 내용이 기대는 실제 동작

설정을 바꾸면 **화면 문구도 함께 고친다** (`frontend/src/data/legal.ts` · `src/pages/legal/*`).

| 화면에 적은 것 | 실제로 정하는 곳 |
|----------------|------------------|
| 회원 파일 24시간 뒤 자동 삭제 | `FILE_RETENTION_HOURS` · `FILE_CLEANUP_MINUTES` (backend 자동 정리) |
| 비로그인 파일은 저장하지 않음 | `routers/upload.py` · `gif.py` · `video.py` (처리 직후 삭제) |
| 요청 문장 · 해석만 검수 후 학습, 사진은 학습에 안 씀 | `LEARNING_COLLECT_REQUESTS` · 콘솔 검수 · `HARD_EXAMPLE_CONF=0`(기본) |
| 서버 로그 14일 | `LOG_RETENTION_DAYS` |
| DB 백업 최근 7일분 | `DB_BACKUP_*` · MariaDB 백업 보관 일수 |
| 문장 해석은 서버 안의 모델 (외부 AI 는 문장만) | `LLM_PROVIDER` (ollama · lora 는 내부, openai · gemini 는 외부 전송) |
| 계정 삭제 시 기록 · 파일 삭제, 학습 문장은 연결 끊기 | 콘솔 회원 삭제 (`services/user_admin.py`) |

**이 중 하나를 바꾸면 방침을 개정해야 한다.** 특히 `HARD_EXAMPLE_CONF` 를 켜면 회원 사진이 학습 후보로 남고,
`LLM_PROVIDER` 를 openai · gemini 로 바꾸면 요청 문장이 외부로 나간다.

## 아직 없는 것

- 회원이 스스로 계정을 지우는 화면 — 지금은 문의처로 요청 → 운영자가 콘솔에서 삭제 ([console-admin.md](./console-admin.md))
- 만 14세 미만 가입 제한 · 법정대리인 동의 절차
- 가입 시 별도 동의 체크박스 (지금은 "가입하면 동의로 본다" 안내)

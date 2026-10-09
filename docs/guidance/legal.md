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
| 요청 문장 · 해석은 검수 후 학습 | `LEARNING_COLLECT_REQUESTS` · 콘솔 검수 |
| 처리 실패 · 인식이 불확실한 요청의 사진은 30일 보관(원인 분석 · 대상 인식 재학습), 계정 삭제 시 바로 삭제 | `FEEDBACK_IMAGE_RETENTION_DAYS`(백엔드 정리) · 빌드 인자 `VITE_FEEDBACK_IMAGE_DAYS`(compose 가 같은 값) · `HARD_EXAMPLE_CONF`(불확실 기준, 기본 꺼짐) · `services/feedback_images.py` |
| 서버 로그 14일 | `LOG_RETENTION_DAYS` |
| DB 백업 최근 7일분 | `DB_BACKUP_*` · MariaDB 백업 보관 일수 |
| 문장 해석은 서버 안의 모델 (외부 AI 는 문장만) | `LLM_PROVIDER` (ollama · lora 는 내부, openai · gemini 는 외부 전송) |
| 계정 삭제 시 기록 · 파일 · 실패 사진 삭제, 학습 문장은 연결 끊기 | 콘솔 회원 삭제 (`services/user_admin.py` → `feedback_images.purge_user`) |

**이 중 하나를 바꾸면 방침을 개정해야 한다.** 특히 `HARD_EXAMPLE_CONF` 를 켜면 실패하지 않은 요청 중 인식이 불확실한 것의 사진도 남고
(방침 문구는 이미 이 경우를 포함한다 — 2026-10-09 개정, 아래),
`LLM_PROVIDER` 를 openai · gemini 로 바꾸면 요청 문장이 외부로 나간다.

## 2026-10-09 개정 — 실패 사진

예전 방침에는 "사진은 학습에 쓰지 않는다", "회원 파일은 24시간 보관"이라고만 적었다. 그런데 회원 요청이 **처리에 실패하면** 원본 사진이
학습 후보로 피드백 폴더(`FEEDBACK_DIR`)에 저장됐다. 이 사진은 24시간 정리 대상이 아니었고, 계정을 지워도 남았다. 동작과 방침이 맞지 않았다.

- 동작: 이런 사진은 `FEEDBACK_IMAGE_RETENTION_DAYS`(기본 30일)가 지나면 주기 정리가 지운다. 콘솔 "지금 정리"도 같이 지운다. 계정을 삭제하면 바로 지운다. 남는 요청 문장 기록은 회원 연결을 끊는다
- 방침: 수집 항목 · 이용 목적 · 보관 기간에 "처리 실패 · 인식이 불확실한 요청의 사진"을 적었다. 운영자만 보고, 외부로 보내지 않는다
- 좋아요 · 싫어요 평가는 사진을 따로 저장하지 않는다(요청 문장 · 평가만)

## 아직 없는 것

- 회원이 스스로 계정을 지우는 화면 — 지금은 문의처로 요청 → 운영자가 콘솔에서 삭제 ([console-admin.md](./console-admin.md))
- 만 14세 미만의 법정대리인 동의 절차 (가입 동의 체크박스에서 만 14세 이상임을 확인받고, 미만은 가입을 받지 않는다)

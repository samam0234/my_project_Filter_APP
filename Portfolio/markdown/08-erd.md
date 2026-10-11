# ERD

그림의 원본은 로컬 Scribble의 `cutnkeep_erd_2026-10-11.html`이다.
그 파일은 Git에 올라가지 않는다. 포트폴리오는 같은 HTML과 PNG를 `Portfolio/assets/erd/`에 두었다.
HTML이 표와 까마귀발 연결을 스크립트로 그리므로, 설명 사이트는 그 파일을 그대로 보여 주고 이 글은 읽는 순서를 붙인다.

그림 기준은 `backend/app/models`와 develop `4468283`(2026-10-11)이다.
Docker는 MariaDB 11, 호스트 개발은 SQLite다.
서비스 DB와 학습 DB는 분리되어 서로 외래 키가 없다.

## 두 구역

왼쪽은 서비스 DB `cutnkeep`이다.

| 테이블 | 역할 |
|--------|------|
| `users` | 회원. 아이디와 이메일은 유일. 비밀번호는 scrypt 해시 |
| `auth_sessions` | 로그인. 기본 키는 토큰의 SHA-256. 원문은 쿠키에만 |
| `auth_codes` | 비밀번호 재설정 1회용 코드. HMAC 해시 |
| `jobs` | 사진, 영상, GIF 작업. `kind`와 `parsed_prompt` JSON |
| `batch_jobs` | 회원 배치. 최대 500장. 진행률과 항목 JSON |

오른쪽은 학습 DB다.

| 테이블 | 역할 |
|--------|------|
| `feedbacks` | 피드백 이벤트. id는 `data/feedback` 사이드카 파일명 |
| `learning_samples` | 콘솔이 검수하는 학습 후보 |

## 관계

실선은 실제 외래 키다. 점선은 다른 DB를 값으로만 가리킨다.

| 관계 | 규칙 |
|------|------|
| users 1 — auth_sessions 0..N | 회원 삭제 시 CASCADE |
| users 1 — auth_codes 0..N | 회원 삭제 시 CASCADE |
| users 0..1 — jobs N | 삭제 시 `user_id`는 NULL |
| users 0..1 — batch_jobs N | 같은 SET NULL. 배치는 회원만 만든다 |
| jobs 1 — feedbacks 0..N | 외래 키 없음 |
| feedbacks 1 — learning_samples 0..2 | prompt와 segment 최대 두 건 |

`learning_samples`는 `(origin_id, kind)`가 유일하다. 같은 출처를 두 번 넣지 않는다.

표기: 막대는 정확히 하나, 원은 없어도 됨, 갈래는 여러 개.
키 표시는 PK, FK, UQ, IX다. NULL은 비어도 되는 열이다.

## 값의 범위

| 열 | 값 |
|----|----|
| `jobs.status` | pending, ok, fallback, failed |
| `jobs.kind` | image, video, gif. 예전 NULL은 image |
| `feedbacks.vote` | like, dislike |
| `feedbacks.source` | user, pipeline_failure |
| `learning_samples.kind` | prompt, segment |
| `learning_samples.source` | correction, like, request, pipeline_failure, pseudo_label |
| `learning_samples.status` | pending, approved, rejected, deleted |
| `learning_samples.split` | train, val |

파일은 경로만 저장한다. 회원 업로드는 `backend/data/uploads`에서 24시간, 실패 사진은 `data/feedback`에서 30일이다.

## 2026-07-27 설계에서 빠진 것

초기 설계의 `parsed_prompts` 테이블은 `jobs.parsed_prompt` JSON이다.
`pseudo_labels` 테이블은 `learning_samples.source = pseudo_label`이다.
`model_versions` 테이블은 없다. 모델은 `backend/models` 파일이고, 채택 기록은 `docs/vaildates`다.

## 그림 다음에 추가된 테이블

이메일 인증 가입이 그림 다음에 들어왔다. 대기 테이블은 `signup_pending`이다.

| 열 | 의미 |
|----|------|
| id | 신청 식별자 |
| email | 유일 |
| username, display_name, password_hash | 인증 전에 보관하는 가입 정보. 비밀번호는 해시 |
| terms_agreed_at | 동의 시각 |
| code_hash, attempts, expires_at, sent_at | 8글자 일련번호. 30분, 5회 |

인증이 끝나면 `users`로 옮기고 이 행은 지운다. 만료되면 주기 작업이 지운다.
기존 `users` 행을 이 변경이 다시 쓰지 않는다. 기동 시 없는 테이블만 만든다.

제품 AI 채팅은 테이블이 없다. 대화를 저장하지 않기 때문이다.
포트폴리오 안내 챗의 대화 표는 없다. 화면 기록은 브라우저 `localStorage`이고, 학습 예시는 JSON 파일이다. 깊이 추론 횟수만 사이트 전용 SQLite `deep_uses`에 남는다. 제품 ERD와는 다른 파일이다.

## 사이트에서 보는 법

ERD 페이지는 HTML을 가로 스크롤이 되는 프레임에 넣는다. 폭은 원본 1780px이다.
옆에 서비스 DB와 학습 DB 설명, 그리고 `signup_pending`이 그림에 없다는 주를 둔다.
PNG는 HTML을 열 수 없을 때의 같은 그림이다.

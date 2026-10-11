# 로컬에서 가입했는데 인증 메일이 안 온다

## 1. 환경
이 PC 에서 직접 띄운 개발 백엔드(`localhost:8000`) + 프런트(`localhost:5173`), 2026-10-11

## 2. 증상
`limjinheng@naver.com` 으로 가입했는데 일련번호 메일이 오지 않는다. 서버(Oracle)에는 그 요청이 도착하지 않았다.

## 3. 원인
- 로컬 `.env` 에 `SMTP_HOST` 가 없어 메일을 보내지 않고 `backend/logs` 에 `[DEV MAIL · SMTP 미설정]` 으로만 남겼다 (개발 모드).
- 화면이 그 사실을 알려 주지 않아 "메일이 안 온다"로 보였다. Gmail 만 되도록 막은 것이 아니다 — 발신 계정과 수신 주소는 별개다.
- (혼동) 테스트로 `limjinheng0120+signup@gmail.com` 같은 `+별칭` 주소를 쓰면 전부 같은 Gmail 받은편지함에 모인다.

## 4. 해결
- 응답에 `mail_delivered` 를 추가하고, 메일이 안 나가는 서버면 인증 화면이 안내한다.
- 로컬에서도 실제 메일을 받으려면 `bash scripts/set_smtp_local.sh` (앱 비밀번호는 숨겨 입력) 후 백엔드 재시작.
- 개발 중 눈으로만 확인하려면 Mailpit(`--profile mail`).

## 5. 검증 명령
```bash
grep "DEV MAIL" backend/logs/app_$(date +%F).log      # 메일이 로그에만 남았는지
curl -s -X POST localhost:8000/api/v1/auth/signup/start ... | grep mail_delivered
```

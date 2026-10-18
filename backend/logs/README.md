# backend/logs — 백엔드 앱 로그

> FastAPI 백엔드의 loguru 파일 로그. 콘솔(stderr) 출력과 같은 내용이 하루 단위 파일로 쌓인다.

학습 · 스크립트 로그는 루트 [`logs/`](../../logs/README.md)에 둔다. **로그 파일은 Git에서 제외된다** (`.gitkeep`과 이 README만 추적).

| 파일 | 내용 |
|------|------|
| `app_YYYY-MM-DD.log` | 하루 단위 로그 (자정 회전, UTF-8) |
| `app_YYYY-MM-DD.<시각>.log` | 자정 회전 때 같은 이름의 파일이 이미 있으면 loguru가 시각을 붙여 따로 남긴 파일 |

| 설정 | 기본 | 설명 |
|------|------|------|
| `LOG_DIR` | `logs` | backend/ 기준 |
| `LOG_RETENTION_DAYS` | 14 | 지나면 자동 삭제 |
| `DEBUG` | true(개발) | true면 DEBUG, 아니면 INFO |

## 무엇이 남나

- 기동 정보 — 환경 · DB 종류 · 학습 DB 모드 · 업로드 · 모델 · 로그 경로
- 요청 처리 — 해석 · 세그 · 검증 · 재시도 결과와 오류
- 메일 — SMTP가 비어 있으면 **보낼 메일 본문이 여기에만** 남는다 (로컬 개발에서 가입 일련번호를 확인하는 곳)
- 콘솔 작업 — 검수 · 삭제를 관리자 이름과 함께
- 경고 — 기동 점검(preflight) · 모델 없음 · 학습 DB 대체

비밀 값(비밀번호 · 토큰 · 앱 비밀번호)은 로그에 남기지 않는다.

## 보는 법

```bash
# 로컬 백엔드
tail -f backend/logs/app_$(date +%F).log
# PowerShell
Get-Content backend/logs/app_$(Get-Date -f yyyy-MM-dd).log -Wait -Encoding utf8

# Docker
docker compose -p cut_and_keep logs -f backend
docker compose -p cut_and_keep logs --no-log-prefix --since 10m backend | grep -E '메일|signup|Error'
```

Docker: `./backend/logs` → `/app/logs` 마운트.

# 공개 배포 대비 보안 강화 — 포트 제한, 보안 헤더, 압축 폭탄 방어, 업로드 자동 정리, DB 자동 백업 / `960bd8e0dad9ac889c7ccfa72229c75b426699ed`

> 브랜치: `feature/security-hardening`  
> 작성일: `2026-10-09 04:03`  
> 작성자: `agent`  
> 파일명: `261009_0403_960bd8e_security-hardening_feature-security-hardening.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(security): 공개 배포 대비 보안 강화 — 포트 제한, 보안 헤더, 압축 폭탄 방어, 업로드 자동 정리, DB 자동 백업` |
| **커밋 번호 (SHA)** | `960bd8e0dad9ac889c7ccfa72229c75b426699ed` |
| **짧은 SHA** | `960bd8e` |
| **브랜치** | `feature/security-hardening` |
| **부모 커밋** | `5a7cc62` |

## 2. 주 커밋 내용

- Docker 포트: backend·MariaDB·Redis·Adminer 를 127.0.0.1 에만 (`BIND_HOST`), 공개는 frontend :80 뿐
- nginx 보안 헤더(CSP · X-Frame-Options · nosniff · Referrer-Policy · Permissions-Policy), `server_tokens off`, 백엔드 중복 헤더 숨김
- 비로그인 속도 제한: nginx 뒤에서 전원이 한 한도를 나눠 쓰던 문제 → `TRUSTED_PROXIES` 대역의 `X-Real-IP` 사용 (콘솔 "이 PC" 판정은 헤더를 믿지 않음)
- 압축 폭탄 방어: 사진 `MAX_IMAGE_PIXELS` · GIF `GIF_MAX_PIXELS` · 영상 `VIDEO_MAX_SIDE` 를 디코딩 전에 검사
- 업로드 자동 정리(`FILE_CLEANUP_MINUTES`) · 서비스 DB 자동 백업(`DB_BACKUP_HOURS`, 최근 7개, 깨진 백업은 버림) — `services/maintenance.py` · `db_backup.py`
- 회원가입·가이드에 보관 기간·학습 이용 안내, 배포 전 점검표 `docs/guidance/security.md`

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "남은 일 · 보안 · 해 줘야 하는 작업". 점검 중 실제 결함 3개 발견: (1) 내부 포트가 모든 네트워크에 열림 (2) 비로그인 한도를 모든 사용자가 공유 (3) "24시간 보관"이 자동으로 지켜지지 않음(정리는 수동 스크립트뿐).

### 3.2 변경 범위
- 추가: `backend/app/services/{maintenance,db_backup}.py`, `docs/guidance/security.md`, `tests/unit/test_security_hardening.py`
- 수정: `config.py`, `ratelimit.py`, `security.py`, `main.py`, 라우터(upload · gif · video), `gif_processor.py`, `video_processor.py`, `docker-compose.yml`, `frontend/nginx.conf`, 가입·가이드 화면, `DATABASE.md`, `.env.example`, `test_preflight.py`

### 3.3 기술 포인트
- 해상도 검사는 Pillow 로 머리말만 읽어(지연 로드) 디코딩 전에 거부, 손상 파일은 이후 단계에 맡김 (배치에서 한 장만 실패하도록)
- SQLite 온라인 백업 API 로 쓰는 중에도 일관된 사본, 백업본도 quick_check
- preflight 테스트가 로컬 `.env`(사용자가 넣은 실제 SECRET_KEY · DEBUG=false)에 흔들리던 것을 기본값 명시로 고정

### 3.4 의도적으로 하지 않은 것
- HTTPS(인증서)·SMTP 실제 설정·개인정보 처리방침 문서(수동, 점검표에 명시), 학습 DB(MariaDB) 자동 백업

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 399 · 프론트 vitest 49
- [x] Docker: 포트 127.0.0.1 바인딩, 보안 헤더(중복 없음), 기동 시 주기 작업 시작·백업 생성 확인

### 4.2 부작용 / 리스크
- 다른 기기에서 backend :8000 에 직접 붙던 사용 방식이 있었다면 `BIND_HOST=0.0.0.0` 필요

### 4.3 후속 작업
- 335d024: 자동 정리가 `.gitkeep` 을 지운 문제 수정

### 4.4 관련 문서
- `docs/guidance/security.md`, `docs/plan/DATABASE.md`

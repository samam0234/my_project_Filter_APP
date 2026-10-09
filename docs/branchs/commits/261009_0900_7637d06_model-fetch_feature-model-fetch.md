# 배포 서버에 없는 LaMa 모델을 자동으로 받기 (SHA-256 확인), 받기 스크립트 / `7637d06f7224bd65fb97b5d6606db41d351a4d41`

> 브랜치: `feature/model-fetch`  
> 작성일: `2026-10-09 09:00`  
> 작성자: `agent`  
> 파일명: `261009_0900_7637d06_model-fetch_feature-model-fetch.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(models): 배포 서버에 없는 LaMa 모델을 자동으로 받기 (SHA-256 확인), 받기 스크립트` |
| **커밋 번호 (SHA)** | `7637d06f7224bd65fb97b5d6606db41d351a4d41` |
| **짧은 SHA** | `7637d06` |
| **브랜치** | `feature/model-fetch` |
| **부모 커밋** | `3371d9b` |

## 2. 주 커밋 내용

- `services/model_fetch.py` — LaMa 받기 · SHA-256 확인 · 임시 파일 → 이름 확정
- 기동 시 자동 받기(`MODEL_AUTO_DOWNLOAD`, 백그라운드), 받는 동안 Telea
- `services/inpaint.py` — 파일이 나중에 생기면 로드
- `scripts/fetch_models.py`

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "LaMa 모델 파일(208MB)은 git 에 없으니 배포 서버에 따로 넣어야 한다 — 이것도 진행".

### 3.2 변경 범위
- 추가: `backend/app/services/model_fetch.py`, `scripts/fetch_models.py`, `tests/unit/test_model_fetch.py`
- 수정: `inpaint.py`, `config.py`, `main.py`, `.env.example`, 문서

### 3.3 기술 포인트
- 체크섬이 다르면 받은 파일을 버림(변조 · 손상 방지), `.part` 로 쓰다 끊겨도 반쪽 파일이 모델로 쓰이지 않음
- 기동을 막지 않는 백그라운드 스레드, Docker 는 bind mount 라 한 번 받으면 호스트에 남음

### 3.4 의도적으로 하지 않은 것
- YOLO · SegFormer 자동 받기 (학습 · 변환 결과물이라 원본 출처가 다름)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 418 통과, 실제 받기 208MB · 12초 · 체크섬 일치

### 4.2 부작용 / 리스크
- 인터넷이 막힌 서버는 자동 받기가 실패(로그만) — `MODEL_AUTO_DOWNLOAD=false` 후 수동 배치

### 4.3 후속 작업
- 품질 개선 (영상·GIF 지우기 · GIF 경계 · 추적 · LoRA · YOLO 재학습 파이프라인)

### 4.4 관련 문서
- `backend/models/README.md`

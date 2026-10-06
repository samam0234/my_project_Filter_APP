# 백엔드 이미지에 세그 모델·LangGraph 포함 / `fefa7376ca442e519a73d4c188e726b7bafd2d98`

> 브랜치: `feature/docker-verify`  
> 작성일: `2026-10-06 17:41`  
> 작성자: `agent`  
> 파일명: `261006_1741_fefa737_docker-vision-langgraph_feature-docker-verify.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(docker): 백엔드 이미지에 세그 모델·LangGraph 포함` |
| **커밋 번호 (SHA)** | `fefa7376ca442e519a73d4c188e726b7bafd2d98` |
| **짧은 SHA** | `fefa737` |
| **브랜치** | `feature/docker-verify` |
| **부모 커밋** | `a7cfb31` (develop) |

## 2. 주 커밋 내용

- Docker 백엔드 이미지에 ultralytics + CPU 전용 torch 설치 → 실제 YOLO 세그
- `requirements.docker.txt` 에 langgraph · langchain-core → 컨테이너도 그래프 실행
- 점검 결과를 `docs/guidance/docker-run.md` 에 기록

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 "다음 할 일" 1번 — push 후 CI 확인 · Docker 재빌드 확인.
- CI: GitHub Actions 실행 `37372370728` (develop `a7cfb31`) — backend · frontend · console 모두 성공 (코드 변경 불필요)
- Docker 재빌드: DB 분리는 정상이었으나 **ultralytics 가 없어 세그가 stub(가짜) 마스크**, langgraph 가 없어 선형 실행

### 3.2 변경 범위

- `backend/Dockerfile`, `requirements.docker.txt`, `docs/guidance/docker-run.md`, `docs/plan/CURRENT_STACK.md`

### 3.3 기술 포인트

- 사용자 결정: ONNX 추론(하드코딩 파트, 직접 구현 대상)은 건드리지 않고 ultralytics 설치로 해결
- torch 는 CPU 전용 인덱스 (CUDA 판 대비 수 GB 작음), 이미지 2.81 GB
- ultralytics 가 opencv-python 을 함께 설치 → headless 와 cv2 가 겹쳐 지우고 headless 로 고정
- 모델 의존성은 Dockerfile 에서만 → CI(`requirements.docker.txt` + 테스트) 는 계속 가벼움

### 3.4 의도적으로 하지 않은 것

- ONNX 추론 구현 (직접 구현 대상으로 남김)
- GPU 이미지 (배포 서버 사양 결정 후)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| 세그 | stub 마스크 | YOLO26s-seg CPU, 97~135 ms |
| 파이프라인 | 선형 | LangGraph |
| 해석 | — | 컨테이너 → 호스트 Ollama, parser=ollama |
| frontend nginx | — | 화면·새로고침 경로·프록시 200 (`/auth/me` 비로그인 401 정상) |

- 첫 요청 14.8 s (Ollama 모델 로드), 다음 요청 1.7 s

### 4.2 부작용 / 리스크

- 이미지가 커짐 (2.81 GB) · 빌드 시간 증가
- CPU 추론이라 큰 이미지·많은 동시 요청에서 GPU 대비 느림

### 4.3 후속 작업

- 배포 서버(Oracle Cloud) 사양에 맞춰 CPU/GPU 이미지 결정

### 4.4 관련 문서

- `docs/guidance/docker-run.md`

# Initial project scaffold / `4b1e6ad`

> 브랜치: `main` → `develop`  
> 작성일: `2026-07-27`  
> 작성자: project

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `chore: initial project scaffold for Cut & Keep` |
| **커밋 번호 (SHA)** | `4b1e6ad17245dffc7628235074cc5260712acfe3` |
| **짧은 SHA** | `4b1e6ad` |
| **브랜치** | `main` (root), 이후 `develop` 기반 |
| **부모 커밋** | `-` (root commit) |

## 2. 주 커밋 내용

- 백엔드 FastAPI 스켈레톤 및 워크플로/서비스 골격 추가
- 프론트엔드 React+Vite 사용자 앱 골격 추가
- `docs/plan` 기획 문서 배치
- scripts, docker-compose, .gitignore, README 초기화

## 3. 상세 내용

### 3.1 배경 / 목적
계획서 기반 폴더·모듈 구조를 코드로 고정해 Phase 1 구현 출발점을 만든다.

### 3.2 변경 범위
- 추가: `backend/`, `frontend/`, `docs/plan/`, `scripts/`, `docker-compose.yml` 등
- 수정: 없음 (초기)
- 삭제: 없음

### 3.3 기술 포인트
- LangGraph 노드/서비스 분리 방향 선반영
- 모델 없이도 stub 마스크로 파이프라인 골격 유지

### 3.4 의도적으로 하지 않은 것
- DB/Repository 계층 (후속 커밋)
- 운영 콘솔 앱
- 실제 YOLO 가중치 번들

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 저장소 초기화 및 브랜치 트리 생성
- [ ] Docker 확인
- 결과: 프로젝트 골격 커밋 완료, feature/* 브랜치 포인터 생성

### 4.2 부작용 / 리스크
- tsbuildinfo 파일이 일시적으로 포함될 수 있음 → 다음 커밋에서 ignore

### 4.3 후속 작업
- DB 계층, Docker 안정화, 문서 허브, 콘솔

### 4.4 관련 문서
- `docs/plan/PROJECT_STRUCTURE.md`
- `docs/plan/LOGIC_STRUCTURE.md`

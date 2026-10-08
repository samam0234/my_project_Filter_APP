# 전체 기능 목록(FEATURES.md) 추가, 빠진 문서 등록 채우기, 문서 등록 자동 검사 / `08db8a12990ea38fae9ed7958a14b8f0711b1572`

> 브랜치: `feature/docs-refresh`  
> 작성일: `2026-10-09 05:33`  
> 작성자: `agent`  
> 파일명: `261009_0533_08db8a1_features-registry_feature-docs-refresh.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 전체 기능 목록(FEATURES.md) 추가, 빠진 문서 등록 채우기, 문서 등록 자동 검사` |
| **커밋 번호 (SHA)** | `08db8a12990ea38fae9ed7958a14b8f0711b1572` |
| **짧은 SHA** | `08db8a1` |
| **브랜치** | `feature/docs-refresh` |
| **부모 커밋** | `d2e363c` |

## 2. 주 커밋 내용

- 코드와 문서를 자동 대조: 엔드포인트 40 · 설정 106 · 화면 11 · 콘솔 메뉴 8 · scripts · training
- 빠진 것 채움: API 문서 1(`GET /console/batches`), `.env.example` 2, 설명 없던 설정 7
- `docs/FEATURES.md` — 전체 기능 목록(화면 · API · 설정 · 코드 · 근거 문서)
- `tests/structure/test_docs_coverage.py` — 문서 등록 자동 검사

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "현재 모든 기능을 문서 등록 먼저 시키고, 빠진 게 있나 확인". 눈으로 훑는 대신 코드에서 목록을 뽑아 문서와 대조했다.

### 3.2 변경 범위
- 추가: `docs/FEATURES.md`, `tests/structure/test_docs_coverage.py`
- 수정: `.env.example`, `docs/API_DOCUMENTATION.md`, `docs/plan/{DATABASE,TESTING}.md`, `docs/guidance/{llm-and-vision,docker-run}.md`, `docs/README.md`, `README.md`

### 3.3 기술 포인트
- 엔드포인트는 경로 변수 이름 차이(`{id}`/`{job_id}`)를 무시하고 대조
- 설정은 `.env.example` 의 주석 예시(`# KEY=`)도 등록으로 인정
- 화면 경로를 하나도 못 읽으면 실패하도록 최소 개수 검사 (그냥 통과 방지), 항목 하나를 지우면 잡히는 것 확인

### 3.4 의도적으로 하지 않은 것
- 날짜가 박힌 기록 문서는 검사 대상에서 제외

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 410 (문서 등록 검사 5건 포함)

### 4.2 부작용 / 리스크
- 이제 새 엔드포인트·설정·화면을 문서 없이 넣으면 테스트가 실패한다 (의도)

### 4.3 후속 작업
- 기능 추가 시 `docs/FEATURES.md` 부터 갱신

### 4.4 관련 문서
- `docs/FEATURES.md`, `docs/plan/TESTING.md`

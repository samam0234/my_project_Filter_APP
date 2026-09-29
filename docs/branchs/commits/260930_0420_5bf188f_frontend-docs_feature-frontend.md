# 사용자 앱 페이지 구조와 사용 흐름 문서화 / `5bf188f3e2bbcb2ce2388b04222014f6a5dafb7c`

> 브랜치: `feature/frontend`  
> 작성일: `2026-09-30 04:20`  
> 작성자: `agent`  
> 파일명: `260930_0420_5bf188f_frontend-docs_feature-frontend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(frontend): 사용자 앱 페이지 구조와 사용 흐름 문서화` |
| **커밋 번호 (SHA)** | `5bf188f3e2bbcb2ce2388b04222014f6a5dafb7c` |
| **짧은 SHA** | `5bf188f` |
| **브랜치** | `feature/frontend` |
| **부모 커밋** | `3ad0396` |

## 2. 주 커밋 내용

- `frontend/README.md` 재작성: 페이지·API 표, 정답 알려주기 → LoRA 흐름, 폴더 구조, 라우터 선택 이유
- `docs/guidance/user-frontend.md` 재작성: 메뉴별 기능, 작업실 사용 흐름, 수동 체크리스트 8항목
- `docs/Architecture/apps.md`: 사용자 앱 페이지 6개 반영

## 3. 상세 내용

### 3.1 배경 / 목적

`3ad0396` 페이지 개편으로 기존 "업로드·프롬프트·피드백 한 화면" 설명이 맞지 않게 되었다.

### 3.2 변경 범위

- 수정된 경로: `frontend/README.md`, `docs/guidance/user-frontend.md`, `docs/Architecture/apps.md`

### 3.3 기술 포인트

- 페이지 표에 페이지별로 호출하는 API 를 적어 백엔드 변경 시 영향 범위를 바로 알 수 있게 함

### 3.4 의도적으로 하지 않은 것

- `docs/vaildates/mvp-checklist.md` 5번(Frontend UI) — `feature/docs` 가 인접 줄을 고쳐 병합 충돌이 나므로
  develop 병합 단계에서 함께 정리

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 문서 링크 경로 확인

### 4.2 부작용 / 리스크

- 없음

### 4.3 후속 작업

- develop 병합 (instance → docs → frontend)

### 4.4 관련 문서

- `docs/branchs/commits/260930_0420_3ad0396_user-app-six-pages_feature-frontend.md`

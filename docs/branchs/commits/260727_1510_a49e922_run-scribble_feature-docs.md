# RUN.md + Scribble ignore / `a49e922`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-27`  
> 파일명: `260727_1510_a49e922_run-scribble_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목** | `docs: add root RUN guide and ignored Scribble scratch folder` |
| **짧은 SHA** | `a49e922` |
| **브랜치** | `feature/docs` |

## 2. 주 커밋 내용

- 루트 `RUN.md` 실행·서버 가이드 추가
- `Scribble/` 개인 메모 폴더 + README, 내용물 gitignore

## 3. 상세 내용

### 3.1 배경 / 목적
루트에서 바로 서버 기동법을 보게 하고, 개인 잡메모는 저장소에 안 올리기 위함.

### 3.2 변경 범위
- 추가: `RUN.md`, `Scribble/README.md`
- 수정: `.gitignore`, `README.md`, docs 링크

### 3.3 기술 포인트
- `Scribble/**` ignore + `!Scribble/README.md` 예외

### 3.4 의도적으로 하지 않은 것
- Scribble 내용을 docs 로 승격하는 자동화

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] README 만 추적, 기타 Scribble 파일 ignore 확인

### 4.2 부작용 / 리스크
없음

### 4.3 후속 작업
없음

### 4.4 관련 문서
- `RUN.md`, `Scribble/README.md`

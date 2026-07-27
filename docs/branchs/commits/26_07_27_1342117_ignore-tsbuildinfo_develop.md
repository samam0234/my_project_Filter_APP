# Ignore TypeScript build info / `1342117`

> 브랜치: `develop`  
> 작성일: `2026-07-27`  
> 작성자: project

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `chore: ignore TypeScript build info files` |
| **커밋 번호 (SHA)** | `1342117c8c54ef85d3e96c2ea17acfa4d9a46257` |
| **짧은 SHA** | `1342117` |
| **브랜치** | `develop` |
| **부모 커밋** | `4b1e6ad` |

## 2. 주 커밋 내용

- `*.tsbuildinfo`를 `.gitignore`에 추가
- 이미 추적 중이던 tsbuildinfo 파일 제거

## 3. 상세 내용

### 3.1 배경 / 목적
TypeScript incremental 빌드 산출물이 저장소를 오염시키지 않도록 한다.

### 3.2 변경 범위
- 수정: `.gitignore`
- 삭제: `frontend/tsconfig.*.tsbuildinfo` (tracking)

### 3.3 기술 포인트
- Vite `tsc -b` 사용 시 생성되는 캐시 파일 정책 정리

### 3.4 의도적으로 하지 않은 것
- 프론트 기능 변경 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 워킹트리 정리
- 결과: develop 기준 깨끗한 스캐폴드 상태 유지

### 4.2 부작용 / 리스크
없음

### 4.3 후속 작업
- backend 계층화 커밋

### 4.4 관련 문서
- `frontend/tsconfig.json` (solution style)

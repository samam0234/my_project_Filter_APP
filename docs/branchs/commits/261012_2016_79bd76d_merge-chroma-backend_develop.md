# feature/chroma-backend → develop 병합 / `79bd76d`

> 브랜치: `develop`  
> 작성일: `2026-10-12 20:16`  
> 작성자: `agent`  
> 파일명: `261012_2016_79bd76d_merge-chroma-backend_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/chroma-backend into develop (no-ff)` |
| **커밋 번호 (SHA)** | `79bd76dad31981a42ba20ef054e3b564cb7e05ae` |
| **짧은 SHA** | `79bd76d` |
| **브랜치** | `develop` |
| **부모 커밋** | `85026c6`, `5c9e2d0` |

## 2. 주 커밋 내용

- `feature/chroma-backend`를 `develop`에 `--no-ff`로 병합했다.
- 문장 해석이 `backend/data/chroma`와 루트 `data/chroma`를 읽게 됐다.
- 기능 커밋은 `8477bf5`다.
- 기록 목록 충돌은 두 파트의 행을 모두 남겨 해결했다.

## 3. 상세 내용

### 3.1 배경 / 목적
확인된 문장을 해석 예시에 한 건 더하는 백엔드 파트를 통합 라인에 붙인다.

### 3.2 변경 범위
- 추가된 경로: `backend/app/services/prompt_chroma.py`, `backend/data/chroma/`, 테스트, 커밋 기록
- 수정된 경로: `prompt_rag.py`, `config.py`, 의존성, `docker-compose.yml`, 안내 문서
- 삭제된 경로: 없음

### 3.3 기술 포인트
`--no-ff`. 코드 충돌은 없었고 커밋 기록 표만 겹쳤다.

### 3.4 의도적으로 하지 않은 것
main 병합, 푸시, 안내 챗 파트. 그 파트는 다음 병합이다.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 파트 커밋 때 RAG·Chroma 테스트 10건이 통과했다.

### 4.2 부작용 / 리스크
Docker 이미지에 chromadb가 추가된다. 이미지 재빌드는 이 병합에서 하지 않았다.

### 4.3 후속 작업
`feature/chroma-portfolio` 병합 후 세 파트를 함께 검토하고 main에 병합한다.

### 4.4 관련 문서
- `docs/guidance/llm-and-vision.md`
- `docs/branchs/commits/261012_2010_8477bf5_prompt-chroma_feature-chroma-backend.md`

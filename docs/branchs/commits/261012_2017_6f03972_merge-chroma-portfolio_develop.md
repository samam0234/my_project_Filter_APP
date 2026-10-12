# feature/chroma-portfolio → develop 병합 / `6f03972`

> 브랜치: `develop`  
> 작성일: `2026-10-12 20:17`  
> 작성자: `agent`  
> 파일명: `261012_2017_6f03972_merge-chroma-portfolio_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: feature/chroma-portfolio into develop (no-ff)` |
| **커밋 번호 (SHA)** | `6f039720f2015a3cdc95f54f2dd93c7f12616927` |
| **짧은 SHA** | `6f03972` |
| **브랜치** | `develop` |
| **부모 커밋** | `6c27f28`, `a961396` |

## 2. 주 커밋 내용

- `feature/chroma-portfolio`를 `develop`에 `--no-ff`로 병합했다.
- 안내 챗이 BM25 결과를 유지한 채 `Portfolio/ai/data/chroma`의 문서 문단과 학습 문답을 보탠다.
- 기능 커밋은 `2296005`다.
- 기록 목록 충돌은 세 파트의 행을 모두 남겨 해결했다.

## 3. 상세 내용

### 3.1 배경 / 목적
루트 피드백 색인과 문장 해석에 이어, 포트폴리오 안내 챗의 할루시네이션을 문서 근거로 줄이는 세 번째 파트를 통합 라인에 붙인다.

### 3.2 변경 범위
- 추가된 경로: `Portfolio/ai/chroma_embed.py`, `Portfolio/ai/chroma_store.py`, `Portfolio/ai/data/chroma/`, `Portfolio/ai/test_chroma_store.py`, 커밋 기록
- 수정된 경로: `guide_graph.py`, `rag_memory.py`, 안내 문구, `Portfolio/ai/requirements.txt`, `Portfolio/.gitignore`, `docs/branchs/README.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트
`--no-ff`. 코드 충돌은 없었고 커밋 기록 표만 겹쳤다. 임베딩 모델은 받지 않는다. 화면 대화 기록은 localStorage, 학습 원본은 `rag_memory.json`이다.

### 3.4 의도적으로 하지 않은 것
이 병합 직후의 기록 커밋은 검토 수정 병합 뒤에 남겼다. main 병합, 푸시, 서버 배포, 제품 모델 변경은 하지 않았다.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 병합 직후 제품 Chroma 테스트 12건과 안내 저장소 테스트 1건이 통과했다. 안내 문구가 있는 페이지 HTML에는 Chroma 문장이 있었다. 클릭 경로는 브라우저로 다시 밟지 않았다.

### 4.2 부작용 / 리스크
글자 해시 벡터는 글자가 거의 안 겹치는 바꿔 쓰기를 BM25보다 잘 잡지 못한다. 안내 검색은 BM25가 우선이다.

### 4.3 후속 작업
문장 해석이 글자 검색 예시를 빼지 않도록 한 `bugfix/chroma-keep-lexical` 병합, 그 다음 main 병합과 푸시.

### 4.4 관련 문서
- `Portfolio/ai/README.md`
- `docs/HANDOVER.md`

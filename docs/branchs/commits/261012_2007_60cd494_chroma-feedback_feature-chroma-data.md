# 확인된 피드백을 Chroma에 색인 / `60cd494`

> 브랜치: `feature/chroma-data`  
> 작성일: `2026-10-12 20:07`  
> 작성자: `agent`  
> 파일명: `261012_2007_60cd494_chroma-feedback_feature-chroma-data.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(data): 확인된 피드백을 Chroma에 색인` |
| **커밋 번호 (SHA)** | `60cd49416d794ca4b8b118ae29251593b6fbc824` |
| **짧은 SHA** | `60cd494` |
| **브랜치** | `feature/chroma-data` |
| **부모 커밋** | `4d816a1` |

## 2. 주 커밋 내용

- 루트 `data/feedback`의 교정·좋아요만 `data/chroma` 컬렉션 `verified_feedback`에 넣는다.
- 파이프라인 실패와 의사 라벨은 색인하지 않는다.
- 임베딩 모델은 받지 않고 한글 2·3글자 벡터(`cutnkeep-char-ngram`, 256차원)를 쓴다.
- 가까운 문장만 유사도 임계값 위로 꺼내고, 파일에서 지워진 문장은 다시 색인할 때 뺀다.
- `python scripts/chroma_feedback.py`로 다시 만든다. 실행 중 생긴 DB 파일은 Git에 올리지 않는다.

## 3. 상세 내용

### 3.1 배경 / 목적
문장 해석이 확인되지 않은 표현을 사실처럼 따르지 않도록, 사용자가 맞다고 한 문장을 벡터 저장소에 둔다. 이 브랜치는 루트 `data`만 담당한다.

### 3.2 변경 범위
- 추가된 경로: `scripts/chroma_embed.py`, `scripts/chroma_feedback.py`, `data/chroma/README.md`, `data/chroma/.gitkeep`, `tests/unit/test_chroma_feedback.py`
- 수정된 경로: `.gitignore`, `data/README.md`, `scripts/README.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트
ChromaDB 1.5.9 영구 클라이언트, 코사인 공간. 유사도는 `1 - distance`. 같은 문장이면 교정이 좋아요보다 우선한다.

### 3.4 의도적으로 하지 않은 것
백엔드 해석 경로 연결, 포트폴리오 안내 챗 연결, 제품 `.env` 변경, 모델 pull, 서버 배포.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: `tests/unit/test_chroma_feedback.py` 2건 통과. 비슷한 한글 문장이 더 가깝고, 실패 사진은 색인되지 않으며, 지운 교정은 다음 색인에서 빠진다.

### 4.2 부작용 / 리스크
`chromadb`가 없는 환경에서는 스크립트가 뜨지 않는다. 의존성 추가는 백엔드 브랜치에서 한다. 이 저장소만으로는 해석 API가 아직 읽지 않는다.

### 4.3 후속 작업
`feature/chroma-backend`가 이 폴더를 읽고, `feature/chroma-portfolio`는 안내 문서용 저장소를 따로 둔다. 파트 커밋이 끝난 뒤 develop에 한 번에 병합한다.

### 4.4 관련 문서
- `data/README.md`
- `data/chroma/README.md`
- `scripts/README.md`

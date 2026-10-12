# 문장 해석에 확인된 Chroma 예시 추가 / `8477bf5`

> 브랜치: `feature/chroma-backend`  
> 작성일: `2026-10-12 20:10`  
> 작성자: `agent`  
> 파일명: `261012_2010_8477bf5_prompt-chroma_feature-chroma-backend.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(backend): 문장 해석에 확인된 Chroma 예시 추가` |
| **커밋 번호 (SHA)** | `8477bf5161ebd015e4ae5f6fe6b8b3b982d63135` |
| **짧은 SHA** | `8477bf5` |
| **브랜치** | `feature/chroma-backend` |
| **부모 커밋** | `4d816a1` |

## 2. 주 커밋 내용

- 승인 예시를 `backend/data/chroma` 컬렉션 `approved_prompts`에 맞춘다.
- 루트 `data/chroma` 컬렉션 `verified_feedback`이 있으면 같이 읽는다.
- 글자 n-gram 결과를 유지하고, 그 목록에 없는 가까운 확인 문장 한 건만 더한다.
- 임베딩 모델은 받지 않는다. Chroma를 열지 못하면 기존 n-gram만 쓴다.
- Docker는 루트 색인을 `/app/shared/chroma`로 마운트한다.

## 3. 상세 내용

### 3.1 배경 / 목적
해석 모델이 확인되지 않은 필드를 따라가지 않도록, 이미 맞다고 본 문장을 벡터 저장소에서 한 건 더 붙인다. 시드와 의사 라벨을 기본 예시에 넣던 구성은 정확도가 내려가 그대로 두지 않는다.

### 3.2 변경 범위
- 추가된 경로: `backend/app/services/chroma_embed.py`, `backend/app/services/prompt_chroma.py`, `backend/data/chroma/`, `tests/unit/test_prompt_chroma.py`
- 수정된 경로: `prompt_rag.py`, `config.py`, `requirements.txt`, `requirements.docker.txt`, `docker-compose.yml`, `.gitignore`, 백엔드 README, `docs/guidance/llm-and-vision.md`, `docs/plan/CURRENT_STACK.md`, `tests/unit/test_prompt_rag.py`
- 삭제된 경로: 없음

### 3.3 기술 포인트
코사인 유사도 기본 하한은 0.55. 의존성은 `chromadb==1.5.9`. 제품 모델과 `.env`는 바꾸지 않는다.

### 3.4 의도적으로 하지 않은 것
루트 피드백 색인 스크립트, 포트폴리오 안내 챗, 모델 pull, 서버 배포, 시드 800건 재포함.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: `test_prompt_rag.py`와 `test_prompt_chroma.py` 10건 통과. 학습 DB가 없어도 공유 색인의 교정 문장을 예시로 꺼낸다.

### 4.2 부작용 / 리스크
Docker 이미지에 chromadb가 추가된다. 글자 벡터라 완전히 다른 말투의 같은 뜻은 n-gram과 같이 놓칠 수 있다. 임계값 아래 예시는 붙이지 않는다.

### 4.3 후속 작업
`feature/chroma-data`의 루트 색인과 `feature/chroma-portfolio`를 커밋한 뒤 develop에 한 번에 병합한다.

### 4.4 관련 문서
- `docs/guidance/llm-and-vision.md`
- `backend/data/chroma/README.md`

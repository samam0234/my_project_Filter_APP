# 글자 검색 예시를 유지한 채 Chroma 한 건을 붙임 / `15fb9af`

> 브랜치: `bugfix/chroma-keep-lexical`  
> 작성일: `2026-10-12 20:19`  
> 작성자: `agent`  
> 파일명: `261012_2019_15fb9af_keep-lexical_bugfix-chroma-keep-lexical.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(backend): 글자 검색 예시를 빼지 않고 Chroma 한 건을 붙임` |
| **커밋 번호 (SHA)** | `15fb9afed53de1c27afb0613102732e11c2760b0` |
| **짧은 SHA** | `15fb9af` |
| **브랜치** | `bugfix/chroma-keep-lexical` |
| **부모 커밋** | `6f03972` |

## 2. 주 커밋 내용

- `merge_hits`가 글자 검색 상위 k건을 그대로 둔다.
- 그 목록에 없는 확인 문장이 있으면 한 건만 뒤에 붙인다. 결과 길이는 k 또는 k+1이다.
- 같은 문장이 벡터 쪽에 다시 나와도 중복으로 넣지 않는다.
- 테스트는 강아지·차 두 건이 남고 사람 문장이 세 번째로 붙는지 확인한다.

## 3. 상세 내용

### 3.1 배경 / 목적
n-gram 점수와 글자 해시 벡터 점수는 같은 척도가 아니다. 벡터 한 건을 넣으려고 글자 검색의 마지막 예시를 빼면, 더 가까운 승인 문장이 빠질 수 있다. develop 병합 뒤 검토에서 이 동작을 고친다.

### 3.2 변경 범위
- 추가된 경로: 이 기록
- 수정된 경로: `backend/app/services/prompt_chroma.py`, `tests/unit/test_prompt_chroma.py`
- 삭제된 경로: 없음

### 3.3 기술 포인트
Chroma 실패 시 n-gram만 쓰는 경로, 하한 0.55, 시드·의사 라벨 제외는 그대로다. 임베딩 모델은 받지 않는다.

### 3.4 의도적으로 하지 않은 것
포트폴리오 안내 검색의 BM25 유지 방식, 제품 `.env`, 모델 pull, 서버 배포, Docker 이미지 재빌드.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: `tests/unit/test_prompt_chroma.py`, `test_prompt_rag.py`, `test_chroma_feedback.py` 12건이 통과했다. 화면 변경은 없다.

### 4.2 부작용 / 리스크
예시는 최대 k+1건이 된다. 프롬프트가 한 줄 더 길어질 수 있다.

### 4.3 후속 작업
develop에 `--no-ff`로 병합한 뒤 main 병합과 푸시.

### 4.4 관련 문서
- `docs/guidance/llm-and-vision.md`
- `backend/app/services/prompt_chroma.py`

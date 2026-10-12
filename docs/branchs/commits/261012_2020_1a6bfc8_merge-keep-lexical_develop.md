# bugfix/chroma-keep-lexical → develop 병합 / `1a6bfc8`

> 브랜치: `develop`  
> 작성일: `2026-10-12 20:20`  
> 작성자: `agent`  
> 파일명: `261012_2020_1a6bfc8_merge-keep-lexical_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: bugfix/chroma-keep-lexical into develop (no-ff)` |
| **커밋 번호 (SHA)** | `1a6bfc8aeef7d9498e667d99dbaf03ce703287c8` |
| **짧은 SHA** | `1a6bfc8` |
| **브랜치** | `develop` |
| **부모 커밋** | `6f03972`, `b3881e7` |

## 2. 주 커밋 내용

- `bugfix/chroma-keep-lexical`를 `develop`에 `--no-ff`로 병합했다.
- 문장 해석은 글자 검색 상위 예시를 빼지 않고, 겹치지 않는 확인 문장 한 건을 뒤에 붙인다.
- 수정 커밋은 `15fb9af`다.
- 충돌은 없었다.

## 3. 상세 내용

### 3.1 배경 / 목적
세 Chroma 파트를 develop에 모은 뒤 검토에서 찾은 예시 탈락을 통합 라인에 반영한다. 수정은 develop에 직접 커밋하지 않고 버그 수정 브랜치를 병합했다.

### 3.2 변경 범위
- 추가된 경로: `docs/branchs/commits/261012_2019_15fb9af_keep-lexical_bugfix-chroma-keep-lexical.md`
- 수정된 경로: `backend/app/services/prompt_chroma.py`, `tests/unit/test_prompt_chroma.py`, `docs/branchs/README.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트
`--no-ff`. 반환 예시는 최대 k+1건이다. Chroma를 열지 못하면 기존 n-gram만 쓴다.

### 3.4 의도적으로 하지 않은 것
main 병합과 푸시는 이 기록 다음에 한다. 제품 `.env`, 모델 pull, 서버 배포, Docker 이미지 재빌드는 하지 않았다.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 병합 트리에서 제품 Chroma 테스트 12건과 안내 저장소 테스트 1건이 통과했다. 충돌 표식은 없다. 화면 변경은 없다.

### 4.2 부작용 / 리스크
해석 프롬프트에 예시가 한 줄 더 들어갈 수 있다.

### 4.3 후속 작업
develop을 main에 `--no-ff`로 병합하고 두 브랜치를 푸시한다.

### 4.4 관련 문서
- `docs/branchs/commits/261012_2019_15fb9af_keep-lexical_bugfix-chroma-keep-lexical.md`

# backend/data/chroma — 승인된 문장 해석 예시 벡터

> 운영 콘솔에서 **승인된** 문장 해석 예시를 담는 Chroma 저장소. 서비스가 직접 만들고 맞춘다.

| 항목 | 값 |
|------|----|
| 컬렉션 | `approved_prompts` |
| 넣는 것 | 학습 DB `learning_samples` 중 승인된 문장(교정 · 좋아요 · 회원 요청) |
| 임베딩 | **모델을 받지 않는다.** 글자 벡터 `cutnkeep-char-ngram` (256차원) |
| 만드는 쪽 | 백엔드 `services/prompt_chroma.py` — 승인 목록이 바뀌면 다시 맞춘다 (약 30초 안) |
| 설정 | `PROMPT_CHROMA_ENABLED` · `PROMPT_CHROMA_DIR`(backend/ 기준 `data/chroma`) · `PROMPT_CHROMA_MIN_SCORE`(0.55) |
| Git | 실행 파일은 올리지 않는다 |

루트 [`data/chroma`](../../../data/chroma/README.md)의 `verified_feedback`(확인된 피드백)과는 **따로**다. 문장 해석은 두 곳을 모두 보고, 글자 검색이 놓친 가까운 문장 한 건을 예시로 더한다.
Chroma를 열지 못하면 글자 n-gram 검색만으로 동작한다.

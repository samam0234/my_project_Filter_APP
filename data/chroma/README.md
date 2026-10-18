# data/chroma — 확인된 피드백 문장 벡터

> 사용자가 **교정하거나 좋아요를 누른** 문장만 담는 Chroma 저장소. 문장 해석이 비슷한 확인 예시를 찾을 때 읽는다.

| 항목 | 값 |
|------|----|
| 컬렉션 | `verified_feedback` |
| 넣는 것 | `data/feedback`의 교정(정답 알려주기) · 좋아요 |
| 넣지 않는 것 | 의사 라벨(`pseudo_labels`) · 파이프라인 실패 사진 |
| 임베딩 | **모델을 받지 않는다.** 한글 2 · 3글자 조각을 256차원으로 해싱한 글자 벡터 (`cutnkeep-char-ngram`) |
| 만드는 쪽 | `python scripts/chroma_feedback.py` (저장소 루트에서) |
| 읽는 쪽 | 백엔드 `services/prompt_chroma.py` — Docker는 `/app/shared/chroma`(`PROMPT_CHROMA_SHARED_DIR`) |
| Git | 실행 파일은 올리지 않는다. 언제든 다시 만들 수 있다 |

## 어떻게 쓰이나

문장 해석의 RAG는 먼저 글자 n-gram TF-IDF로 승인 문장을 찾는다. 그 검색이 놓친 확인 문장이 있으면, 이 저장소와 [`backend/data/chroma`](../../backend/data/chroma/README.md)에서 **가까운 한 건**을 예시로 더한다. 코사인이 `PROMPT_CHROMA_MIN_SCORE`(0.55) 미만이면 붙이지 않는다.

학습 DB에 아직 들어가지 않은 확인 문장도 여기서는 예시가 될 수 있다.

```bash
python scripts/chroma_feedback.py                                   # 다시 색인
python scripts/chroma_feedback.py --query "가운데 사람만 남기고 배경 블러" --k 3   # 가까운 예시 확인
```

벡터 함수는 [`scripts/chroma_embed.py`](../../scripts/chroma_embed.py)다. 백엔드 · 이 폴더 · 포트폴리오 안내가 **같은 이름과 차원**을 써야 서로 읽을 수 있다.

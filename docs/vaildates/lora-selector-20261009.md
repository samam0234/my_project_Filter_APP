# LoRA 재학습: 개수 + 위치 선택자 조합 문장 (2026-10-09)

> 실행: `python training/lora/seed/build_compositional.py` → `python scripts/retrain_lora.py --force` · 실행 이름 `user_261009_2023`
> 원자료: [`lora_retrain_selector_20261009.json`](./lora_retrain_selector_20261009.json) (평가셋별 정확도 · 오답 전부)
> 앞 단계: [`lora-compositional-20261009.md`](./lora-compositional-20261009.md)

## 요약

- 앞 재학습 뒤 남은 오답은 대부분 **개수와 위치가 섞인 선택자**였다
  - "오른쪽 개 두 마리만": 정답은 count 2 인데 rank 2 를 붙였다
  - "새 두 마리 중에 큰 새만": 정답은 largest 인데 속성 "large bird" 로 답했다
- 조합형 생성기에 이 유형을 넣었다(선택자 218문장, 전체 1,100문장). 넣기 **전에** 새 평가셋 `eval_fresh3`(30문장)를 먼저 썼다
- `eval_fresh3` 전 항목 일치는 **33.3% → 96.7%** 다(고친 19 · 망가진 0). 홀드아웃은 87.5% → 97.5% 다
- 전체 +29문항, 최대 하락은 eval_ext 1문항이다. 판정을 통과해 배포본을 교체했다. 이전 배포본은 `backend/models/lora_prev_261009_2115` 에 있다

## 추가한 문장 (`build_compositional.py` 6번 묶음)

| 꼴 | 예 | 정답 selector |
|----|----|---------------|
| 위치 + 개수 | "앞쪽 와인잔 두 개만 남기고 배경 지워줘" | front · count 2 |
| N개 중 비교 | "티비 3대 중에 왼쪽에 있는 티비만 지워줘" | left · count 1 |
| N개 중 크기 | "정지 표지판 세 개 중에 큰 정지 표지판만 지워줘" | largest · count 1 |
| 하나 + 위치 | "가장 작은 책 하나만 남기고 나머지 투명하게" | smallest · count 1 |
| 가깝다 · 멀다 | "가장 가까운 차 한 대만" / "가장 먼" | front / back |
| 영어 | "keep the 2 dogs on the right", "remove the bigger of the 3 cats", "crop the closest bicycle" | right · 2 / largest · 1 / front · 1 |

- 세는 단위(명 · 마리 · 대 · 개)를 대상에 맞춰 붙인다
- 개수 + 위치 문장에서는 rank 를 붙이지 않는다. 테스트가 이를 확인한다

## 결과 (전 항목 일치)

| 평가셋 | 배포본 → 새 후보 | 고침 · 망가짐 |
|--------|------------------|---------------|
| eval (40) | 95.0% → 97.5% | |
| eval_ext (56) | 91.1% → 89.3% | 1 · 2 |
| eval_distractor (47) | 91.5% → 93.6% | |
| eval_holdout (40) | 87.5% → **97.5%** | 5 · 1 (p = 0.22) |
| eval_fresh (30) | 90.0% → **100%** | |
| eval_fresh2 (40) | 87.5% → 92.5% | 3 · 1 (p = 0.63) |
| **eval_fresh3 (30, 선택자, 새)** | 33.3% → **96.7%** | 19 · 0 |
| 승인 val (1) | 100% → 100% | |

- 대상 정확도는 거의 그대로다. eval_distractor 만 100% → 97.9% 로 1문항 내려갔다
- 바뀐 것은 선택자와 효과다
- 학습 사례 2,718건(레코드 4,773). 평가 문장과 같은 41건은 학습에서 뺐다

## 남은 오답

- `eval_fresh3`
  - "가운데 서 있는 두 사람만 선명하게 강도 40" → blur 를 remove_bg 로 답했다. "선명하게"가 앞의 선택자에 묻혔다
- eval_ext
  - "강쥐만 남겨줘" → `rat`. 줄임말 · 은어 어휘가 없다
  - 띄어쓰기 없는 "사람만남기고배경제거" → blur
- holdout
  - "사람은 두고 나머지 물체들은 모두 날려줘" → 올바른 JSON 을 내지 못했다(빈 답)
  - 서비스에서는 이때 키워드 파서로 내려간다

## 한계

- `eval_fresh3` 도 생성기를 만든 사람이 같은 정답 규칙으로 썼다. 다만 생성 템플릿보다 **먼저** 썼고 말투를 다르게 했다
  - 예: "앞줄 사람 세 명", "왼쪽 끝 사람 두 명은 빼고", "오른편"
  - 그래도 실제 사용자 문장이 쌓이면 그쪽 점수를 우선한다
- 기본 `LLM_PROVIDER` 는 ollama 그대로다. LoRA 가 쓰이는 것은 `LLM_PROVIDER=lora` 이거나 혼합(`PROMPT_SECOND_OPINION`)일 때뿐이다

## 되돌리기

```bash
mv backend/models/lora backend/models/lora_rejected_261009_selector
mv backend/models/lora_prev_261009_2115 backend/models/lora
```

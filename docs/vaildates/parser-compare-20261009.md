# 문장 해석기 비교 — Ollama 체인 vs LoRA vs 혼합 (2026-10-09)

> 실행: `python scripts/experiments/parser_compare.py --out docs/vaildates/parser_compare_20261009.json`
> 원자료: [`parser_compare_20261009.json`](./parser_compare_20261009.json) (평가셋 · 파서별 정확도 · 호출 수 · 오답 전부)
> 앞 단계: [`lora-compositional-20261009.md`](./lora-compositional-20261009.md)

## 왜

LoRA 를 조합형 문장으로 다시 학습한 뒤, 처음 보는 40문장에서 Ollama 첫 답보다 높게 나왔다. 하지만 서비스가 실제로 쓰는 것은 Ollama 하나가 아니다. **Ollama + 키워드 파서 체인**이다. 그래서 같은 조건으로 비교했다.

LoRA 는 greedy 생성이라 같은 문장에 늘 같은 답을 낸다. 지금 체인에 LoRA 만 넣으면 다시 물어도 같은 답이라 투표가 의미 없다(체인 + LoRA = LoRA 단독). 그래서 **혼합** 방식을 더했다.

## 비교한 것

| 이름 | 방식 |
|------|------|
| heuristic | 키워드 파서만 (LLM 없음) |
| chain_ollama | **지금 서비스 기본**. Ollama 에 한 번 묻고, 키워드 파서와 대상이 다르면 최대 3번까지 묻는다. 키워드 파서도 한 표 |
| lora | LoRA 단독 |
| chain_hybrid | LoRA 에 먼저 묻는다. 키워드 파서와 대상이 다를 때만 Ollama 에 한 번 더 묻고, 셋이 투표한다. 셋이 다 다르면 LoRA 답을 쓴다 |

- 모든 파서에서 RAG 예시를 붙이지 않았다(같은 조건)
- GPU 는 RTX 4070 SUPER 하나다. Ollama(gemma4:e4b)와 LoRA 가 GPU 를 같이 쓴 상태에서 쟀다

## 결과 (전 항목 일치)

| 평가셋 (문장 수) | heuristic | chain_ollama | lora | **chain_hybrid** |
|------------------|-----------|--------------|------|------------------|
| eval (40) | 70.0% | 87.5% | 95.0% | **95.0%** |
| ext (56) | 78.6% | 87.5% | 91.1% | **92.9%** |
| distractor (47) | 89.4% | 87.2% | 91.5% | **91.5%** |
| holdout (40) | 85.0% | **97.5%** | 87.5% | 90.0% |
| fresh (30) | 80.0% | 80.0% | **90.0%** | 86.7% |
| fresh2 (40) | 62.5% | 70.0% | 87.5% | **90.0%** |
| **전체 (253)** | 77.9% | 85.4% | 90.5% | **91.3%** |
| 대상 정확도 (전체) | 95.7% | 96.8% | 98.0% | **98.8%** |
| 문장당 시간 | 0초 | 6.9초 | 2.5초 | **3.0초** |
| Ollama 호출 (253문장) | — | 293번 | — | **15번** |

- 혼합 방식은 전체 정확도와 대상 정확도가 가장 높다. 속도는 지금 서비스보다 2배 넘게 빠르다
  - 키워드 파서와 같은 답이 나오면 LoRA 한 번으로 끝난다
  - Ollama 는 253문장 중 15번만 불렸다
- **holdout 에서는 지금 서비스(97.5%)가 혼합(90.0%)보다 높다.** 이 셋은 Ollama 체인 규칙을 만든 뒤 쓴 문장이라 체인에 유리할 수 있다
- fresh 의 chain_ollama 는 80.0% 다. 이전 문서(leak-diagnosis)의 "체인 96.7%" 는 **대상 정확도**였고, 이번 대상 정확도는 90.0% 다. 이번에는 RAG 없이 쟀다

## 한계 — 기본값을 바꾸지 않은 이유

- **평가 문장이 LoRA 학습 설계에 영향을 줬다.** 조합형 학습 문장은 fresh 의 오답 유형을 보고 만들었다. fresh2 도 같은 작성자가 같은 정답 규칙으로 썼다
  - 실제 사용자 문장(운영 콘솔에서 승인된 val)은 아직 1개뿐이다
- **Docker 이미지에서는 LoRA 를 못 돌린다.** 백엔드 이미지는 CPU 전용 torch 에 transformers · peft 가 없다
  - 위 시간은 GPU 기준이다. CPU 에서 1.5B 모델은 문장당 수 초~십수 초가 걸린다
- GPU 하나에서 Ollama(gemma4:e4b 약 9.6GB)와 LoRA(1.5B bf16 가중치만 약 3GB)를 같이 올리면 12GB 카드에서는 빠듯하다

## 켜는 방법 (호스트 · GPU)

```env
LLM_PROVIDER=lora
LORA_BASE_MODEL=../training/models/qwen2.5-1.5b-instruct
PROMPT_SECOND_OPINION=ollama
PROMPT_VOTES=2
```

`tests/unit/test_prompt_chain.py` 가 동작을 확인한다. 첫 답은 LoRA 로, 키워드 파서와 갈릴 때만 Ollama 로 묻고, 같으면 Ollama 를 부르지 않는지 본다.

## 다음

- 승인된 실제 사용자 문장이 쌓이면(val) 같은 스크립트로 다시 비교한다. 혼합이 계속 앞서면 GPU 서버의 기본값으로 바꾼다
- Docker 에서 쓰려면 백엔드 이미지에 GPU torch + transformers + peft 를 넣는 선택형 빌드가 필요하다

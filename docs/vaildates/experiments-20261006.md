# 실험 결과 — 2026-10-06

완성도 점검 5번 "검증의 한계"(평가셋 40건뿐 · 실사용 데이터 없음 · 부하 미검증)를 직접 실험한 기록.
환경: Windows 11, RTX 4070 SUPER, 호스트 uvicorn, Ollama gemma4:e4b, 세그 `yolo26s-seg.pt`.

| # | 실험 | 스크립트 · 결과 파일 | 결과 요약 | 반영 |
|---|------|----------------------|-----------|------|
| 1 | 프롬프트 해석 확장 평가 (56건) | `training/lora/eval_parser.py --eval-file seed/eval_ext.jsonl` | Ollama 85.7% · LoRA v2 80.4% — 규격 밖 단어로 파싱 실패 | 어휘 정규화 → **91.1% · 83.9%** |
| 2 | 인스턴스 선택 (실제 이미지 600장, 정답 폴리곤) | `scripts/experiments/selection_e2e.py` → `selection_e2e_20261006.json` | 명확한 문항 64.0% — 멀리 찍힌 작은 인스턴스가 "맨 왼쪽"이 됨 | 작은 인스턴스 제외 → **71.6%** |
| 3 | 마스크 정제(GrabCut) 속도·품질 | `scripts/experiments/refine_speed.py` | 전체 이미지 GrabCut 중앙값 690 ms, 정답 대비 IoU 개선 없음 | ROI GrabCut → 216 ms, IoU 동일 |
| 4 | 동시 요청 부하 | `scripts/experiments/load_test.py` → `load_test_20261006*.json` | 오류 0, 처리 중 `/health` < 13 ms, 처리량 상한 약 21~23 건/분 (LLM 병목) | 3번으로 단건 지연 7.4 → 6.2 s |

---

## 1. 프롬프트 해석 — 확장 평가셋

`training/lora/seed/eval_ext.jsonl` 56건: 오타·띄어쓰기("사람만남기고배경제거", "지워죠"), 구어("누끼 따줘", "강쥐"),
영어·혼용("person 만 남기고 background 지워줘"), 남김/지움이 헷갈리는 표현("사람 지우고 배경만 남겨"),
새 대상(화분·꽃병·곰인형·기차·피자). 학습 데이터·기존 평가셋과 겹치지 않음. 라벨이 애매한 4건은 뺐다.

| 파서 | 정규화 전 | 정규화 후 |
|------|-----------|-----------|
| ollama gemma4:e4b | 85.7% (파싱 실패 3) | **91.1%** (실패 0) |
| LoRA v2 (배포) | 80.4% | 83.9% |
| 키워드 | 42.9% | — |

- 원인: Ollama 가 effect `"keep"` 을 내 해석 전체가 실패(→ 키워드 파서), LoRA 가 `"flower pot"`·`"train car"` 등 COCO 밖 이름
- 반영: `prompt_spec.canonical_target` · `EFFECT_ALIASES` ([`llm-and-vision.md`](../guidance/llm-and-vision.md#어휘-정규화-모든-파서-공통))
- 사용자 문장 학습(LoRA v3) 효과는 승인 8건이라 측정 안 됨 → [`training/lora/README.md`](../../training/lora/README.md)

## 2. 인스턴스 선택 — 실제 이미지

프롬프트 해석을 빼고 정답 selector 를 넣어 **세그 + 선택 규칙**만 잰다.
`training/datasets/cutnkeep_seg_5k/images/val` 600장, 같은 클래스(사람·개·고양이·차)가 2개 이상인 장면,
정답 = 라벨 폴리곤에 같은 정렬 규칙 적용 (이미지의 1% 미만 인스턴스는 정답 후보 제외). 고른 마스크와 IoU ≥ 0.5 면 정답.
기준 값 차이가 작은 문항(위치 3% · 면적 10% 미만)은 "애매"로 따로 센다.

| 시나리오 | 이전 | **작은 인스턴스 제외 후** |
|----------|------|---------------------------|
| 왼쪽 첫 번째 | 68.9% | 77.0% |
| 왼쪽에서 두 번째 | 53.0% | 64.3% |
| 오른쪽 첫 번째 | 69.2% | 75.2% |
| 가운데 | 74.2% | 78.9% |
| 제일 큰 | 80.6% | 80.6% |
| 제일 작은 | 38.4% | 53.6% |
| **전체 (명확 1320문항)** | **64.0%** | **71.6%** |

- 원인: YOLO 가 정답 라벨에 없는 먼 곳의 작은 사람까지 찾아 "맨 왼쪽"·"제일 작은"이 그쪽으로 감
- 반영: `instance_selector._salient` — 위치로 고를 때 가장 큰 후보의 20% 미만이면서 이미지의 1% 미만인 인스턴스 제외
  (0.05~0.3 비교 중 최고. 정답 정의(1%)와 같은 절대 기준만 쓰면 74.2% 지만 실험 기준에 맞춘 값이라 상대 기준을 택함)
- 남은 오답(명확 1320 중): **검출 누락 202** (사람 검출 재현율 83%) · **순서 오류 173** (병합·추가 검출·라벨 누락)
  → 세그 모델 자체(학습 데이터·모델 크기) 문제. 다음 단계는 YOLO 재학습 또는 더 큰 모델 비교
- "맨 앞/맨 뒤" 는 깊이 정답이 없어 측정하지 않음

## 3. 마스크 정제(GrabCut) 속도·품질

`effect_applier` 가 요청당 약 2 s 로 세그(0.04 s)의 50배였다. 원인은 원본 전체에서 도는 GrabCut.
결과는 어차피 원 마스크 주변 띠로 잘리므로 마스크 bbox + 여백(ROI)에서만 돌린다.

| 방식 (사람 마스크 80장) | 시간 중앙값 | 정답 폴리곤 대비 IoU |
|--------------------------|-------------|----------------------|
| 정제 없음 (YOLO 원본) | 0 | 0.760 |
| GrabCut 전체 이미지 (이전) | 690 ms | 0.746 |
| **GrabCut ROI (현재)** | **216 ms** | 0.750 |

- ROI 와 전체 결과의 일치도 IoU 중앙값 0.976
- **GrabCut 이 정답 대비 IoU 를 올리지 못했다.** 단 COCO 폴리곤은 거칠어 머리카락 같은 세밀한 경계가 오히려 감점될 수 있어
  정제를 없애지는 않았다 — 눈으로 비교(A/B)하는 후속 확인 필요
- 반영: `effects.GRABCUT_ROI` · `GRABCUT_ROI_MARGIN` · `GRABCUT_MAX_SIDE`

## 4. 동시 요청 부하

비로그인 업로드(저장 없음) 8건씩, 요청마다 다른 프롬프트, 처리 중 0.5 s 마다 `/health`.

| 동시 | 처리량 (건/분) | p50 | p95 | `/health` 최대 | 오류 |
|------|----------------|-----|-----|-----------------|------|
| 1 | 7.3 → **9.6** | 7.4 → **6.2 s** | 14.1 → 8.2 s | 3.5 ms | 0 |
| 2 | 17.2 | 6.7 s | 10.0 s | 5.9 ms | 0 |
| 4 | 22.8 → 21.7 | 8.7 → 6.8 s | 14.0 → 15.4 s | 6.1 ms | 0 |
| 8 | 20.8 | 15.6 s | 23.1 s | 12.3 ms | 0 |

(→ 오른쪽은 ROI GrabCut 적용 후 재측정, 1·4 동시만)

노드별 중앙값 (ms): prompt_analyzer **5,900~6,200** (동시 8 에서 12,800) · segmentor 35 · effect_applier 2,090 → **1,040**

- 서버는 처리 중에도 다른 요청에 바로 응답 (스레드풀 실행 확인)
- 동시 4 이상에서 처리량이 늘지 않음 — **Ollama LLM 이 한 번에 하나씩** 처리해서 대기열이 생긴다 (세그는 35 ms 라 병목 아님)
- 개선 방향: `LLM_PROVIDER=lora` (요청당 1~2 s, 정확도 83.9% vs 91.1%), Ollama `OLLAMA_NUM_PARALLEL`, 같은 문장 해석 캐시
- 이 PC 기준 수치. 배포 서버(Oracle Cloud)는 GPU 유무에 따라 다시 측정해야 한다

## 재현

```powershell
# 저장소 루트, training venv. load_test 는 실서버(uvicorn :8000)가 떠 있어야 한다
python training/lora/eval_parser.py --eval-file training/lora/seed/eval_ext.jsonl --parsers heuristic,ollama
python scripts/experiments/selection_e2e.py --limit 600 --report docs/vaildates/selection_e2e_20261006.json
python scripts/experiments/refine_speed.py --limit 80
python scripts/experiments/load_test.py --levels 1,2,4,8 --per-level 8
```

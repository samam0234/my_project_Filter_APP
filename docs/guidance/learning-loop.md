# 새 학습 내용이 반영되는 곳 — RAG · LangGraph · LangChain · LoRA · 세그 모델

사용자 교정, 운영자 승인, 새 어휘(예: 건물·하늘), 어려운 사례가 **어디로 들어가 무엇을 바꾸는지** 한 장으로 정리한다.
근거 수치는 [`docs/vaildates/leak-diagnosis-20261008.md`](../vaildates/leak-diagnosis-20261008.md).

```
 사용자 👍/교정 · 회원 요청 ─┐
                            ▼
                    학습 DB(learning_samples) ── 운영 콘솔 "학습 데이터" 검수(승인/수정/삭제)
                            │ 승인된 것만
        ┌───────────────────┼─────────────────────────┐
        ▼                   ▼                         ▼
   ① RAG 색인(30초)     ② LoRA 재학습 시드          ③ 승인 val → 재학습 판정(eval)
   LLM 지시문에 예시      scripts/retrain_lora.py     eval · ext · distractor · holdout · fresh
        │
        ▼
   ④ 해석 체인(LangChain) ─► ⑤ LangGraph 파이프라인 ─► 마스크(겹침 덜어내기) ─► 결과
                                   │
                                   └─ ⑥ 어려운 사례(HARD_EXAMPLE_CONF) ─► 학습 후보(콘솔 검수) ─► 세그 재학습 후보
```

## ① RAG — 교정이 바로 반영된다 (재학습 없이)

- 승인된 `correction · like · request` 문장이 **30초 안에** 색인되어(`PROMPT_RAG_REFRESH_SECONDS`) 비슷한 요청의 LLM 지시문에 예시로 붙는다
- 새 어휘·새 말투를 가르치는 가장 빠른 길: 운영 콘솔에서 해당 문장을 **정답 고쳐서 승인**
- 시드 문장도 지식 베이스로 쓸 수 있다 (`PROMPT_RAG_SOURCES=correction,like,request,seed`). 방해물 학습 문장
  `training/lora/seed/train_distractor.jsonl`(180문장: "X 말고 Y만" 같은 패턴)이 그 예 — 효과는 검증 문서의 문장 해석 절

## ② LoRA — 새 패턴을 모델에 굳히기

```bash
python scripts/retrain_lora.py              # 승인 문장이 LORA_RETRAIN_MIN_NEW(200) 이상 쌓였는지 확인
python scripts/retrain_lora.py --force      # 기준 무시하고 한 바퀴 (점검용)
python scripts/retrain_lora.py --deploy     # 평가에서 이기면 배포본 교체
```

- 시드: `seed/train.jsonl`(800) + `seed/train_distractor.jsonl`(180) + `seed/train_compositional.jsonl`(899, `build_compositional.py`) 이 자동으로 들어간다 (`train_lora.py --seed-file` 여러 개)
- 평가셋 6개 = `eval`(40) · `eval_ext`(56) · `eval_distractor`(47, 방해물 문장) · `eval_holdout`(40, 규칙을 만든 뒤 처음 본 문장) · `eval_fresh`(30) · `eval_fresh2`(40, 조합형 시드를 만들기 전에 쓴 문장).
  **어느 평가셋에서도 1문항보다 더 떨어지면 채택하지 않는다** — 방해물 문장에서 악화되면 배포되지 않는다
- 같은 문장이 학습과 평가에 동시에 있으면 평가에서 빼지 않고 **학습에서 뺀다** (`drop_eval_leaks`, 점수 부풀림 방지)
- 새 어휘(건물·하늘…)를 LoRA 가 모르면 낱개 물체로 잘못 해석한다 → 어휘를 늘렸다면 재학습
- 2026-10-08 재학습 결과(방해물 문장 78.7→95.7%, 처음 본 문장 73.3%): [`lora-retrain-20261008.md`](../vaildates/lora-retrain-20261008.md)
- 2026-10-09 조합형 문장 재학습(새 40문장 전 항목 일치 50.0→87.5%, Ollama 첫 답 75.0%): [`lora-compositional-20261009.md`](../vaildates/lora-compositional-20261009.md). 체인 + LoRA 조합은 아직 재지 않아 기본 provider 는 ollama

## ③ 새 어휘를 추가하는 방법 (예: "가로등")

1. 세그 모델이 아는 클래스인가? COCO 80 은 YOLO, 풍경 14종은 SegFormer(`services/prompt_spec.STUFF_GROUPS`), 그 밖은 오픈 보캐브
2. `prompt_spec.py`: 묶음(`STUFF_GROUPS`)과 한국어·동의어 별칭(`_STUFF_ALIASES`)을 추가 — LLM 지시문(`SYSTEM_PROMPT`)의 어휘 목록과 예시도 같이
3. `services/heuristic_targets.py` 의 `_EXTRA` 에 일상어 추가 (한 글자 낱말은 오탐 위험 — `_ONE_CHAR_OK` 참고)
4. 평가: `parse_rounds.py` 에 그 어휘를 쓴 문장을 평가셋에 추가 → 규칙을 만든 뒤 쓴 문장은 `eval_holdout` 에 둔다

## ④ 해석 체인 (LangChain Core)

`PROMPT_CHAIN=langchain` — LLM 한 번 호출 → **키워드 파서(`heuristic_targets`)와 대상이 같으면 그대로 확정**(호출 1번, 지연 없음) →
다르면 최대 `PROMPT_VOTES` 번 더 물어 **LLM 답들 + 키워드 파서 한 표**로 다수결 (`services/prompt_chain.py`).
RAG 예시는 모든 호출에 똑같이 붙는다. **기본값은 langchain** — 처음 보는 30문장에서 대상 정확도 86.7% → 96.7%(호출 평균 1.4번). 사진·배치·영상이 같은 체인을 쓴다.

## ⑤ LangGraph 파이프라인

`prompt_analyzer → preprocessor → segmentor → validator → (재시도) → feedback_collector → effect_applier`

- segmentor: 선택한 인스턴스에서 **다른 인스턴스가 차지한 픽셀을 덜어낸다**(`MASK_EXCLUSIVE`), 입력은 CLAHE 끔이 기본이고 재시도는 반대쪽 입력 + 낮은 신뢰도
- 결과 `meta.leak` 에 위험 신호(`conf_min` 등)가 남는다 — 정답 없이 알 수 있는 값 중 **`conf_min` 만** 섞임·오선택과 상관이 있었다 (AUC 0.74)
- 신호로 재시도를 태우는 것은 **효과가 없어서**(쌍 비교 변화 ≈ 0) 쓰지 않는다

## ⑥ 어려운 사례 수집 → 세그 모델 개선 재료

`HARD_EXAMPLE_CONF=0.4` 처럼 켜면, 처리는 ok 였지만 고른 인스턴스의 최소 신뢰도가 그 값 미만인 **로그인 회원 요청**이
`feedback_collector` 로 가서 학습 후보로 저장된다 (`meta.hard_example=true`). 콘솔 "학습 데이터"에서 검수하고, 모인 이미지는
의사 라벨(`scripts/pseudo_labeling.py`)·YOLO 미세 조정의 재료가 된다.

- 0.4 기준으로 사진의 약 10% 가 걸리고 그중 약 31% 가 실제 섞임/오선택 (무작위의 2.4배) — 데이터 수집 효율이 2배 이상
- **회원 이미지가 더 저장되는 일**이라 기본은 꺼져 있다 (개인정보 안내·보관 기간 `FILE_RETENTION_HOURS` 와 함께 결정)

모인 사진에 YOLO-seg 폴리곤 라벨을 달면(CVAT · Label Studio 등, `images/` · `labels/`) 재학습 루프에 넣는다:

```bash
python scripts/retrain_yolo.py --collect-only                  # COCO 어려운 사례 + 일반 사진 준비 (한 번)
python scripts/retrain_yolo.py --skip-collect --extra <라벨 폴더> # 이어 학습 → 섞임 평가 · mAP → 판정
python scripts/retrain_yolo.py --skip-collect --extra <라벨 폴더> --deploy   # 채택이면 backend/models 교체 (백업)
```

COCO 만으로 돌린 첫 실행은 두 번 다 불채택이었다 — 서비스 모델이 이미 COCO 로 학습돼 새 정보가 없다
([`yolo-retrain-20261009.md`](../vaildates/yolo-retrain-20261009.md)). **COCO 밖 실패 사진**이 수백 장 모였을 때 의미가 있다.

## 무엇이 효과 없었나 (다시 시도하지 않도록)

| 시도 | 결과 |
|------|------|
| 입력 크기 960/1280 · NMS 0.5 · 신뢰도 0.15/0.4 | 이득 없음 또는 역효과 (1280 은 두 사람이 합쳐짐 15→29%) |
| 더 큰 YOLO(l, x) | 유의한 이득 없음, 1.9~2.6배 느림 · s 는 유의하게 나쁨 |
| GrabCut / CLAHE 켜기 | 섞임·경계·IoU 모두 손해 → 기본 끔 |
| "붐빔(맞닿음·덜어낸 비율)" 신호 | 거의 무의미 (AUC 0.5~0.65) |
| 낮은 신뢰도에서 재시도 | 결과 변화 없음 |

# LangGraph Workflow

정본은 [plan/LOGIC_STRUCTURE.md](plan/LOGIC_STRUCTURE.md) §3–4.

```
prompt_analyzer → preprocessor → segmentor → validator
       ├─ ok → effect_applier → END
       ├─ fallback (retry) → segmentor
       └─ fail → feedback_collector → effect_applier → END
```

| 노드 | 하는 일 | 주요 코드 |
|------|---------|-----------|
| `prompt_analyzer` | 문장 → `ParsedPrompt` (target·effect·selector). LLM 실패 시 키워드 파서 | `services/prompt_llm.py`, `prompt_lora.py`, `prompt_spec.py` |
| `preprocessor` | 긴 변 1280 리사이즈 + CLAHE | `services/image_processor.py` |
| `segmentor` | YOLO-seg 인스턴스 → 요청 라벨만 → **selector 로 인스턴스 선택**. 재시도면 조건을 바꿈 (아래) | `services/segmentation.py`, `instance_selector.py` |
| `validator` | 마스크 면적·confidence 로 ok / fallback / failed. 빈 마스크면 "요청 대상을 찾지 못함" 안내. 재시도 뒤에는 **더 나은 시도 채택** | `services/validator.py`, `nodes._keep_best_attempt` |
| `effect_applier` | 마스크를 원본 해상도로 맞춘 뒤 GrabCut 정제 + 효과. `remove_object` 는 inpaint | `services/effects.py` |
| `feedback_collector` | 실패 케이스를 DB + `data/feedback/` 에 저장 (학습 재료). **비로그인(`persist=False`)은 저장하지 않음** | `services/feedback_service.py` |

## 재시도 (fallback → segmentor)

같은 입력으로 다시 돌리면 결과가 같으므로 조건을 바꾼다 (`nodes.RETRY_CONFIDENCE_SCALE`).

| 시도 | 입력 이미지 | 신뢰도 기준 | `segment_strategy` |
|------|-------------|-------------|--------------------|
| 1차 | CLAHE 전처리 | `min_confidence` (0.25) | `default` |
| 2차 | CLAHE 없는 원본 축소본 | × 0.6 (0.15) | `retry_no_clahe_lowconf` |

두 시도 중 (상태 ok > fallback > failed, 품질 점수) 가 더 나은 쪽을 채택한다 — 완화한 조건이 더 나쁜 마스크를 만들면 1차를 유지.

## 실행 · 성능

- 업로드 라우터는 파이프라인을 **스레드풀**(`run_in_threadpool`)에서 돌린다 → 처리 중에도 다른 요청 즉시 응답
  (처리 중 `/health` 평균 11 ms 확인). YOLO 추론은 `Segmentor._lock` 으로 직렬화
- 기동 직후 백그라운드에서 세그 모델 로드 + 빈 이미지 추론 1회 (`PRELOAD_MODELS`, `main._preload_models`)
  → 서버 시작 후 첫 요청 71 s → 4.5 s (로컬 RTX 4070 SUPER, 측정 2026-10-04)
- 노드마다 소요 시간을 누적해 `meta.timings`(ms)와 로그 `pipeline job=… timings(ms)=…` 에 남긴다

## 결과 meta 추적 정보

| 키 | 내용 |
|----|------|
| `prompt_parser` | 실제로 쓰인 파서 (ollama · lora · heuristic …) |
| `labels` · `detected` | 선택된 라벨 · 필터 전 감지 라벨 |
| `selection` | 인스턴스 선택 요약 (후보 수 · 선택 수 · 색 점수) |
| `segment_strategy` · `attempts` · `chosen_attempt` | 채택된 시도의 전략 · 시도 횟수 · 채택 번호 |
| `timings` | 노드별 소요 시간 (ms) |

코드: `backend/app/workflows/`

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
| `segmentor` | YOLO-seg 인스턴스 → 요청 라벨만 → **selector 로 인스턴스 선택** | `services/segmentation.py`, `instance_selector.py` |
| `validator` | 마스크 면적·confidence 로 ok / fallback / failed. 빈 마스크면 "요청 대상을 찾지 못함" 안내 | `services/validator.py` |
| `effect_applier` | 마스크를 원본 해상도로 맞춘 뒤 GrabCut 정제 + 효과. `remove_object` 는 inpaint | `services/effects.py` |
| `feedback_collector` | 실패 케이스를 DB + `data/feedback/` 에 저장 (학습 재료). **비로그인(`persist=False`)은 저장하지 않음** | `services/feedback_service.py` |

결과 `meta` 에 남는 추적 정보: `prompt_parser`(쓰인 파서), `labels`(선택된 라벨),
`detected`(필터 전 감지 라벨), `selection`(후보 수·선택 수·색 점수).

코드: `backend/app/workflows/`

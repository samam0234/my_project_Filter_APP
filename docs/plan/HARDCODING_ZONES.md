# 하드코딩 구간 · 완성도 부족분 맵

**목적:** “솔직한 완성도 스케치”의 빈 칸을 어디에 채우는지 한눈에 본다.  
**주석 형식:** 코드 안 `# ---` … `하드코딩 파트 부분 : [작업 이름]` 블록.

완료된 본선 로직(휴리스틱 키워드, 이펙트 본체, YOLO `.pt` 경로 등)에는  
새 하드코딩 주석을 **넣지 않았다.** 미구현·스캐폴드만 표시.

---

## 1. 완성도 스케치 → 부족분

| 영역 | 대략 현재 | 부족 | 채울 하드코딩 (우선) |
|------|-----------|------|----------------------|
| 골격·인프라·문서 | ~80% | ~20% | 코드 아님 (.env, 배포, 모델 파일 배치) |
| Phase1 단일 이미지 | ~70% | ~30% | **LLM 연결**, (선택) ONNX 추론 |
| 비전 품질·학습 루프 | ~30% | ~70% | 데이터셋 수집, **평가**, **pseudo label**, YOLO fine-tune 실행 |
| Phase2 (배치/LoRA/SAM2) | ~20% | ~80% | **배치 워커**, **LoRA**, **DINO+SAM2** |
| 네가 채울 실습 빈칸 | (선구현 많음) | — | 아래 “미완 하드코딩”만 숙제 칸으로 유지 |

**권장 작업 순서 (부족 % 효율)**

1. Phase1 구멍: `LLM 프롬프트 분석 연결`  
2. 모델 파일 배치 + (선택) `ONNX predict`  
3. 학습 데이터 + `train_segment` 실행 (주석 구역 아님, training 가이드)  
4. `evaluate_model` 메트릭  
5. Phase2: batch → pseudo → LoRA → SAM2  

---

## 2. 하드코딩 파트 목록 (코드에 표시됨)

| 작업 이름 | 파일 | 메우는 부족 축 |
|-----------|------|----------------|
| LLM 프롬프트 분석 연결 | `backend/app/workflows/nodes.py` | Phase1 ~30% |
| LLM Settings 사용 안내 | `backend/app/core/config.py` | (nodes 와 세트) |
| ONNX 세션·predict 분기 | `backend/app/services/segmentation.py` | Phase1 / Docker 경량 |
| ONNX 전·후처리 루프 | `backend/app/utils/onnx_utils.py` | 위와 동일 |
| Grounding DINO + SAM2 | `backend/app/services/segmentation.py` | Phase2 비전 |
| 배치 실처리 워커 | `backend/app/tasks/batch_tasks.py` | Phase2 배치 |
| LoRA 학습 루프 | `training/lora/train_lora.py` | Phase2 / 학습 |
| LoRA 운영 진입점 래퍼 | `scripts/fine_tune_lora.py` | Phase2 |
| 의사 라벨 생성 루프 | `scripts/pseudo_labeling.py` | 학습 데이터 생산 |
| 세그 품질 평가 메트릭 | `scripts/evaluate_model.py` | 학습 검증 |

---

## 3. 의도적으로 안 건드린 것 (이미 동작)

다음 위치의 기존 구현은 **완료된 본선**으로 보고 새 하드코딩 블록을 넣지 않음.

- `parse_prompt_heuristic` 키워드·effect 동의어 (이미 동작)
- `Segmentor._predict_yolo` 본문
- `effects.py` blur/remove_bg/crop
- LangGraph 그래프 연결, upload 라우터 e2e
- DB job/feedback 기본 CRUD

이 부분을 다시 “빈 숙제”로 만들고 싶으면 별도 요청으로 비우기.

---

## 4. 주석 템플릿 (통일)

```text
# ---
# 제목 (하드코딩 파트 부분 : [작업 이름])
# [관련 작업 임무 및 역할]
#   ...
# [기능하고 연결된 변수 및 함수]
#   ...
# [작성해야 하는 방식 및 규칙]
#   ...
# [코드 방식 힌트]
#   ...
# ---
```

사이 삽입 시 위아래 **빈 줄 1줄** 유지.

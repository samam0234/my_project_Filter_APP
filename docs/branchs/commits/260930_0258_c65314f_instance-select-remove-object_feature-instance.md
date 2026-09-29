# 특정 인스턴스 선택과 물체 지우기 추가 / `c65314ff64de9ccc989fafb63cab6666fe8cb5a0`

> 브랜치: `feature/instance`  
> 작성일: `2026-09-30 02:58`  
> 작성자: `agent`  
> 파일명: `260930_0258_c65314f_instance-select-remove-object_feature-instance.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(yolo): 특정 인스턴스 선택과 물체 지우기 추가` |
| **커밋 번호 (SHA)** | `c65314ff64de9ccc989fafb63cab6666fe8cb5a0` |
| **짧은 SHA** | `c65314f` |
| **브랜치** | `feature/instance` |
| **부모 커밋** | `80fa40b` (develop) |

## 2. 주 커밋 내용

- **A 규격:** `ParsedPrompt.selector`(position·rank·count·attributes), `effect=remove_object`
- **A 규격 공용화:** 지시문·정규화를 `services/prompt_spec.py` 로 분리 (LoRA 학습과 공유)
- **B 선택:** `services/instance_selector.py` — 인스턴스별 마스크 중 위치·순서·개수로 선택
- **C 색 속성:** 인스턴스(부위) 영역 HSV 색 비율로 "red helmet", "neon yellow vest" 매칭
- **D 지우기:** 마스크 팽창 + Telea inpaint, 큰 이미지는 축소 작업 후 마스크 영역만 합성
- 마스크 품질: 원본 해상도 보정, GrabCut 파편·어두운 옷 잘림 방지

## 3. 상세 내용

### 3.1 배경 / 목적

사용자 dislike 케이스(`aead2558`, "맨 앞에 빨간색 안전모와 형광색 조끼를 입은 남성을 제외하고
전부 제거")에서 사람 7명 + car 가 모두 남았다. YOLO 는 클래스까지만 알려 주므로
"어느 사람인가"는 인스턴스 비교(선택) 단계가 필요하다. 추가 학습으로 해결되는 문제가 아니다.
또 "X 지워줘"를 표현할 효과가 없어 항상 "X 를 남기기"로 처리했다.

### 3.2 변경 범위

- 추가된 경로:
  - `backend/app/services/instance_selector.py`, `backend/app/services/prompt_spec.py`
  - `tests/unit/test_instance_selector.py`
- 수정된 경로:
  - `backend/app/schemas/request.py` (`InstanceSelector`, `POSITIONS`, `EFFECTS`)
  - `backend/app/core/constants.py` (`EffectType.REMOVE_OBJECT`)
  - `backend/app/services/prompt_llm.py` (규격은 prompt_spec 에서 import)
  - `backend/app/services/segmentation.py` (`Instance`, `union_mask`, `SegmentationResult.instances`)
  - `backend/app/services/effects.py` (`apply_remove_object`, GrabCut 띠 제한·핵심부 고정)
  - `backend/app/workflows/nodes.py` (휴리스틱 selector, segmentor 선택, 해상도 보정)
  - `backend/app/workflows/state.py`, `graph.py` (`selection` meta)
  - `frontend/src/types/index.ts` (`InstanceSelector` 타입)
  - `tests/unit/test_effects.py`, `test_prompt_heuristic.py`, `test_prompt_llm.py`
- 삭제된 경로: 없음

### 3.3 기술 포인트

| 선택 | 기준 |
|------|------|
| front / back | 0.6 × (bbox 아래끝 / H) + 0.4 × (면적 / 최대면적) — 카메라에 가까울수록 아래·크게 |
| left / right / center | 마스크 무게중심 |
| largest / smallest | 마스크 면적 |
| rank | 위치 정렬의 N번째 ("오른쪽에서 두 번째") |
| count 만 있음 | 면적 큰 순 (눈에 띄는 것부터) |
| attributes | 통과 후보 안에서 위치 정렬, 통과 없으면 최고점 1개 |

- 적용 순서: 색 속성 필터 → 위치 정렬 → rank·count
- 효과 의미: `remove_object` 만 "선택 대상을 지움", 나머지는 "선택 대상을 남김" → `mode` 필드 불필요
- 선택자 일부가 잘못돼도 target/effect 는 살림 (`normalize_selector` 는 잘못된 부분만 버림)
- 빨강 채도 하한 140: 얼굴 피부가 "red helmet" 에 걸리던 문제(0.07~0.09 → 0.00~0.05)

### 3.4 의도적으로 하지 않은 것

- 학습형 inpaint (LaMa) — Telea 는 큰 물체에서 번짐
- Grounding DINO 텍스트 그라운딩 (Phase 2) — 지금은 색 규칙
- 색 외 속성 (키, 성별, 행동 등)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 전체 122개 통과
- [x] 실제 `yolo26s-seg.pt` + 사용자 사진(`aead2558`)
  - 원 요청 → 사람 6명 중 맨 앞 1명만 (속성 점수 0.36 vs 나머지 ≤ 0.02)
  - "빨간 안전모 쓴 사람 지워줘" / "왼쪽에 있는 사람 지워줘" / "흰색 차 없애줘" → 해당 인스턴스만 지움
  - "오른쪽 사람만 남기고 배경 블러" → 차 뒤 사람 1명만 선명
- [x] gemma4:e4b 가 확장 규격(selector·remove_object) 8개 샘플 모두 형식 준수
- [ ] Docker 확인 (미실시)

### 4.2 부작용 / 리스크

- Telea inpaint 는 큰 물체 자리에 번진 자국이 남음
- 색 판정은 조명·그림자에 민감 (HSV 범위는 `instance_selector.COLOR_RANGES` 에서 튜닝)
- 겹친 인스턴스는 YOLO 마스크가 서로 조금 섞일 수 있음

### 4.3 후속 작업

- E: LoRA 로 selector 생성 학습 (시드 데이터 + 평가)
- 학습형 inpaint, Grounding DINO

### 4.4 관련 문서

- `docs/plan/AI_MODEL_STRATEGY.md`
- `docs/branchs/commits/260930_0153_d4ba085_yolo-target-filter_feature-yolo.md`

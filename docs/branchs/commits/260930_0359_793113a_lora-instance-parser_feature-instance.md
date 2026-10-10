# 인스턴스 선택 프롬프트 LoRA 학습·평가·서빙 추가 / `793113a02e9313faba6c635d4b000860982d7b7c`

> 브랜치: `feature/instance`  
> 작성일: `2026-09-30 03:59`  
> 작성자: `agent`  
> 파일명: `260930_0359_793113a_lora-instance-parser_feature-instance.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 인스턴스 선택 프롬프트 LoRA 학습·평가·서빙 추가` |
| **커밋 번호 (SHA)** | `793113a02e9313faba6c635d4b000860982d7b7c` |
| **짧은 SHA** | `793113a` |
| **브랜치** | `feature/instance` |
| **부모 커밋** | `3970b1b` |

## 2. 주 커밋 내용

- 시드 학습 데이터 생성기(800건)와 손으로 쓴 평가셋(40건)
- `train_lora.py` 하드코딩 구간(샘플 정책·템플릿·target_modules) 구현 + VRAM 절약
- `eval_parser.py`: heuristic · ollama · base · lora 를 같은 평가셋으로 채점
- `LLM_PROVIDER=lora` 서빙 (`services/prompt_lora.py`)
- `count` 규칙 통일, 부위 어휘·별칭 확장

## 3. 상세 내용

### 3.1 배경 / 목적

기존 LoRA 데이터(의사 라벨 5,000건)는 "X만 크롭" 같은 단순 요청뿐이라
selector(위치·순서·개수·색)와 `remove_object` 를 배울 예제가 없었다.
사용자 요청대로 "특정 인물·사물을 확실히 인지"하도록 추가 학습 데이터를 만들어 학습했다.

### 3.2 변경 범위

- 추가된 경로:
  - `backend/app/services/prompt_lora.py`
  - `training/lora/eval_parser.py`
  - `training/lora/seed/build_seed.py`, `train.jsonl`, `eval.jsonl`
- 수정된 경로:
  - `backend/app/services/prompt_spec.py` (`LORA_TEMPLATE`, `parsed_to_json`, count 규칙)
  - `backend/app/services/prompt_llm.py` (`lora` provider 분기)
  - `backend/app/services/instance_selector.py` (hoodie·raincoat 등 부위, `PART_ALIASES`)
  - `backend/app/core/config.py` (`LORA_BASE_MODEL`, `LORA_ADAPTER_PATH`)
  - `training/lora/dataset.py`, `train_lora.py`, `README.md`
  - `scripts/fine_tune_lora.py` (주간 인자 = 새 기본값)
  - `.env.example`, `requirements.txt` (선택 의존성 주석)
  - `docs/plan/CURRENT_STACK.md`, `HARDCODING_ZONES.md`
  - 테스트: `test_prompt_llm.py`, `test_lora_dataset.py`, `test_instance_selector.py`

### 3.3 기술 포인트

- **규격 단일화:** 학습 레이블·서빙 입력 모두 `prompt_spec` 을 거침 → 학습/서빙 형식 불일치 없음
- **응답 전용 loss:** 지시·프롬프트 토큰은 -100 → 변환만 학습
- **라벨 위생:** 의사 라벨의 숫자 없는 블러 문장에 붙은 intensity 20 을 15 로 교정
- **VRAM:** bf16 + LoRA fp32, gradient checkpointing, batch 4 × 누적 2
  (첫 시도는 Ollama·백엔드와 GPU 를 공유해 OOM)
- **평가 공정성:** 평가 문장이 학습 시드에 없도록 검사 (v2 첫 실행에서 1건 누수 발견 → 문구 교체 후 재학습)
- **count 규칙 통일:** 숫자·위치 표현이 있을 때만. 지시문은 "단수면 1", 시드·평가는 "숫자만"으로 달랐던 것을 맞춤

### 3.4 의도적으로 하지 않은 것

- 기본 provider 를 lora 로 전환 (품질은 gemma 가 5%p 높음 — 사용자 선택)
- Ollama 로 어댑터 서빙 (Qwen2 safetensors 어댑터 미지원 → transformers 서빙)
- 평가셋 문장 구조를 시드에 흉내 내기 (일반화 측정 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 파서 | 완전 일치 | 건당 |
|------|-----------|------|
| heuristic | 35.0% | 0 s |
| ollama gemma4:e4b | 92.5% | 5.4 s |
| base Qwen2.5-1.5B | 7.5% | 3.2 s |
| LoRA v1 (시드 600) | 77.5% | 1.2 s |
| **LoRA v2 (시드 800)** | **87.5%** | 1.8 s |

- [x] pytest 전체 132개 통과
- [x] `LLM_PROVIDER=lora` 파이프라인: 사용자 사진에서 맨 앞 1명 선택 / 왼쪽 두 번째 지우기 정상,
      두 번째 요청부터 파이프라인 전체 1.6 s (첫 요청 모델 로드 51 s)
- [x] 실제 서버(ollama) 업로드 API 로 같은 두 요청 정상
- [ ] Docker 확인 (미실시)

### 4.2 부작용 / 리스크

- LoRA 오답 유형: 문장 속 다른 명사에 끌림 ("말 사진에서 사람", "가방 든 사람 말고 가방")
- LoRA 서빙은 백엔드 프로세스에 1.5B 모델을 올림 (GPU ~3 GB) — Ollama 와 동시 사용 시 VRAM 주의
- 로컬 16 GB RAM 에서 학습·Ollama·백엔드를 동시에 돌리면 페이징 부족 가능

### 4.3 후속 작업

- 사용자 dislike 코멘트에 정답 JSON 을 적는 UI (정답 데이터 축적)
- 명사 혼동 케이스 시드 보강 후 v3, 필요 시 3B 베이스
- develop 병합

### 4.4 관련 문서

- `training/lora/README.md` (평가 표·서빙 방법)
- `docs/branchs/commits/260930_0258_c65314f_instance-select-remove-object_feature-instance.md`

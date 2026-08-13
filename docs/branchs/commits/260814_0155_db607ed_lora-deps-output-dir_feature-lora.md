# LoRA 학습 루프 의존성 가드와 출력 디렉터리 준비 / `db607ed2cce7f20c773abbe468fbd3c589f49a08`

> 브랜치: `feature/lora`  
> 작성일: `2026-08-14 01:55`  
> 작성자: `agent`  
> 파일명: `260814_0155_db607ed_lora-deps-output-dir_feature-lora.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(lora): 학습 루프 의존성 가드와 출력 디렉터리 준비` |
| **커밋 번호 (SHA)** | `db607ed2cce7f20c773abbe468fbd3c589f49a08` |
| **짧은 SHA** | `db607ed` |
| **브랜치** | `feature/lora` |
| **부모 커밋** | `a61f8edf8a93c5498fe8f92068c4a6b79d0fcdab` |

## 2. 주 커밋 내용

- LoRA 하드코딩 구간에 `torch` / `transformers` / `peft` import 가드 추가
- 의존성 미설치 시 안내 메시지 후 `SystemExit(1)` 로 종료
- `args.output` 디렉터리 자동 생성 (`mkdir parents=True`)
- 학습 루프 본문(데이터셋·학습·어댑터 저장)은 아직 스캐폴드 상태 유지

## 3. 상세 내용

### 3.1 배경 / 목적

하드코딩 파트에 학습 루프를 채우기 전, 학습 의존성 존재 여부와  
어댑터 출력 경로를 먼저 확보해 이후 구현이 바로 이어지도록 한다.

### 3.2 변경 범위

- 수정된 경로:
  - `training/lora/train_lora.py`
- 추가된 경로: 없음
- 삭제된 경로: 없음

### 3.3 기술 포인트

- import 는 하드코딩 블록 내부에서 lazy 로 수행 (스캐폴드 실행 시 학습 의존성 필수)
- `ImportError` 시 `training/requirements-training.txt` 확인 안내
- 스캐폴드 안내 출력 후 `SystemExit(0)` 동작은 유지

### 3.4 의도적으로 하지 않은 것

- `build_dataset` → `inject_lora` → `train` → `save_adapter` 본문 구현
- 데이터셋·하이퍼파라미터 튜닝, 평가 루프
- develop 병합 · 원격 푸시

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [ ] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 코드 스캐폴드 보강 커밋. peft/torch 미설치 환경에서는 하드코딩 구간 진입 시 의존성 오류로 종료될 수 있음.

### 4.2 부작용 / 리스크

- 이전에는 의존성 없이 스캐폴드 안내만 출력하고 종료했으나,  
  이제는 하드코딩 구간 import 가 먼저 실행되어 학습 의존성이 필요함.
- `json` / `datetime` 등은 후속 루프용으로 선 import 했으며 아직 미사용.

### 4.3 후속 작업

- 학습 루프 본문 구현 (dataset → LoRA inject → train → adapter 저장)
- (선택) `git push -u origin feature/lora`
- 완료 후 develop 병합 시 `git merge --no-ff`

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
- `training/requirements-training.txt` (존재 시)

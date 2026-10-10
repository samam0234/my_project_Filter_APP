# 요청 대상 외 객체가 마스크에 섞이는 필터 수정 / `d4ba08500fb3e1bbe54aef1a64f8230a7064913d`

> 브랜치: `feature/yolo`  
> 작성일: `2026-09-30 01:53`  
> 작성자: `agent`  
> 파일명: `260930_0153_d4ba085_yolo-target-filter_feature-yolo.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(yolo): 요청 대상 외 객체가 마스크에 섞이는 필터 수정` |
| **커밋 번호 (SHA)** | `d4ba08500fb3e1bbe54aef1a64f8230a7064913d` |
| **짧은 SHA** | `d4ba085` |
| **브랜치** | `feature/yolo` |
| **부모 커밋** | `027f06d` (develop) |

## 2. 주 커밋 내용

- 요청 target 라벨만 마스크에 합침 ("all" 이면 전부)
- `min_confidence` 를 대상 인스턴스에도 적용
- 대상이 없으면 stub 타원 대신 빈 마스크 → failed · 피드백 저장, 결과는 원본 유지
- "요청한 대상(X)을 찾지 못했습니다. 감지된 대상: …" 안내 메시지
- 필터 전 감지 라벨 `detected` 를 state · meta · 피드백 meta 에 기록
- 가짜 YOLO 단위 테스트 6개

## 3. 상세 내용

### 3.1 배경 / 목적

기존 조건은 "대상 라벨이 아니고 **그리고** confidence 가 낮으면 제외"였다.
즉 대상이 아니어도 confidence 가 높으면 마스크에 들어갔다.
실제 사용자 dislike 케이스(job `aead2558`, "맨 앞 … 남성을 제외하고 전부 제거")에서
target=person 인데 `car`(0.77) 가 함께 남았다.

또 대상을 하나도 못 찾으면 중앙 타원 stub 마스크를 돌려줘,
모델이 모르는 대상(예: bus)을 요청해도 엉뚱한 결과가 "ok" 로 나왔다.

### 3.2 변경 범위

- 추가된 경로: `tests/unit/test_segmentation_filter.py`
- 수정된 경로:
  - `backend/app/services/segmentation.py` (`_predict_yolo` 필터, `SegmentationResult.detected`)
  - `backend/app/workflows/nodes.py` (segmentor·validator·effect·feedback 노드)
  - `backend/app/workflows/state.py`, `backend/app/workflows/graph.py` (`detected`)
- 삭제된 경로: 없음

### 3.3 기술 포인트

- stub 은 **모델이 아예 없을 때만** 사용 (데모용 역할 유지)
- 빈 마스크 → `score_mask` 가 failed → 기존 그래프 경로(feedback_collector → effect_applier) 그대로 탐
- effect_applier 는 빈 마스크면 원본 복사 (전부 투명 / 전부 블러 방지)
- 피드백 meta 에 `labels`·`detected` 가 남아 학습 데이터로 "무엇을 요청했고 무엇이 보였는지" 추적 가능

### 3.4 의도적으로 하지 않은 것

- 같은 클래스 안에서 특정 인스턴스 하나 고르기 ("맨 앞 남자만") — 후속 설계
- `min_confidence`(0.25) 값 조정
- `ImageProcessor.run` (배치용 비그래프 경로) 의 빈 마스크 처리

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] pytest 전체 통과 (신규 6개 포함)
- [x] 실제 `yolo26s-seg.pt` + 사용자 이미지(`aead2558` before.jpg) 확인
  - person → person 5개만 (car 제외)
  - car → car 1개
  - bus → 빈 마스크, detected = car, person
- [ ] Docker 확인 (미실시)

### 4.2 부작용 / 리스크

- 이전에 stub 으로 "ok" 가 나오던 요청이 이제 failed 로 나옴 (의도된 변화)
- 서빙 모델이 5클래스라 LLM 이 COCO 이름(bus 등)을 내면 대상 없음이 자주 발생 → 어휘 정합 작업 필요

### 4.3 후속 작업

- 인스턴스 선택(위치·크기·속성) 단계 설계
- LLM 어휘와 서빙 모델 클래스 정합
- `feature/llm`, `feature/backend` 와 함께 develop 병합

### 4.4 관련 문서

- `docs/plan/HARDCODING_ZONES.md`
- `docs/plan/AI_MODEL_STRATEGY.md`

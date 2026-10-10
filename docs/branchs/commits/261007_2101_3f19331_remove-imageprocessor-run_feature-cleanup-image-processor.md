# 인스턴스 선택을 건너뛰던 ImageProcessor.run 삭제 / `3f1933141b7bef1bef5f233b928f8dd9f3c6cbf1`

> 브랜치: `feature/cleanup-image-processor`  
> 작성일: `2026-10-07 21:01`  
> 작성자: `agent`  
> 파일명: `261007_2101_3f19331_remove-imageprocessor-run_feature-cleanup-image-processor.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `refactor(pipeline): 인스턴스 선택을 건너뛰던 ImageProcessor.run 삭제` |
| **커밋 번호 (SHA)** | `3f1933141b7bef1bef5f233b928f8dd9f3c6cbf1` |
| **짧은 SHA** | `3f19331` |
| **브랜치** | `feature/cleanup-image-processor` |
| **부모 커밋** | `76cf3cf` |

## 2. 주 커밋 내용

- `ImageProcessor.run` · `process_batch_generator` · `PipelineOutput` 삭제 (호출처 0)
- `ImageProcessor` 는 전처리(CLAHE) + 공용 세그멘터 보관만 담당
- `effects.py` 모듈 설명, `docs/plan/LOGIC_STRUCTURE.md` 배치 메모리 설명을 실제 흐름으로 수정

## 3. 상세 내용

### 3.1 배경 / 목적
`d80b809` 에서 배치를 `run_pipeline` 으로 옮기며 "이후 정리 후보"로 남겨 둔 코드. `run()` 은 인스턴스 선택·원본 크기 복원·재시도를 건너뛰므로 누가 다시 호출하면 "왼쪽에서 두 번째 사람" 이 "사람 전체" 로 바뀌는 버그가 되살아난다.

### 3.2 변경 범위
- 수정: `backend/app/services/image_processor.py`, `backend/app/services/effects.py`, `docs/plan/LOGIC_STRUCTURE.md`

### 3.3 기술 포인트
- `nodes._get_processor()` 싱글톤·`preprocess`·`segmentor` 속성은 그대로 → 노드·영상·테스트 영향 없음

### 3.4 의도적으로 하지 않은 것
- 클래스 이름 변경 (호출처가 많아 이름은 유지)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과

### 4.2 부작용 / 리스크
- 없음 (외부 호출처 없음 확인)

### 4.3 후속 작업
- `feature/open-vocab-tune`

### 4.4 관련 문서
- `docs/plan/LOGIC_STRUCTURE.md`

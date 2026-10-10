# 지정하지 않은 인물·동물·물체가 대상에 섞여 안 지워지는 문제 — 정답 주석 실험으로 원인을 찾아 기본값 전환 / `03eb9692e2c08cfbb189512be7d77c4ad055a21f`

> 브랜치: `feature/leak-diagnosis`  
> 작성일: `2026-10-08 10:01`  
> 작성자: `agent`  
> 파일명: `261008_1001_03eb969_leak-gt-eval-mask-defaults_feature-leak-diagnosis.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(segmentation): 지정하지 않은 인물·동물·물체가 대상에 섞여 안 지워지는 문제 — 정답 주석 실험으로 원인을 찾아 기본값 전환` |
| **커밋 번호 (SHA)** | `03eb9692e2c08cfbb189512be7d77c4ad055a21f` |
| **짧은 SHA** | `03eb969` |
| **브랜치** | `feature/leak-diagnosis` |
| **부모 커밋** | `70dc550` |

## 2. 주 커밋 내용

- 정답 주석(COCO 인스턴스 폴리곤)으로 "안 지워지고 합쳐지는" 증상을 직접 재는 평가기 `leak_eval` 추가, 74개 라운드로 원인 분리
- 원인 3개 확인: GrabCut 경계 정제가 이웃 조각을 끌어옴 · CLAHE 가 검출/선택을 해침 · 인스턴스 마스크 겹침으로 다른 사람/물체 픽셀이 대상에 포함
- 기본값 전환: `MASK_EXCLUSIVE=subtract` · `MASK_GRABCUT=false` · `PREPROCESS_CLAHE=false`
- `mask_exclusion.py` 신규(겹침 덜어내기·금지 구역·위험 신호), 세그 결과에 `others` 추가, 영상도 같은 규칙
- 재시도 전략을 "반대쪽 전처리 + 낮은 신뢰도"로 일반화

## 3. 상세 내용

### 3.1 배경 / 목적
LLM 이 대상을 정확히 가리켜도 언급하지 않은 인물·동물·물체가 남길 객체와 합쳐져 안 지워지는 문제. 원인을 추측하지 않고 정답 주석 대비 수치로 가려내기 위함.

### 3.2 변경 범위
- 추가: `backend/app/services/mask_exclusion.py`, `scripts/experiments/leak_eval.py`, `scripts/experiments/parse_rounds.py`, `tests/unit/test_mask_exclusion.py`, `training/lora/seed/eval_distractor.jsonl`(47)
- 수정: `config.py`, `effects.py`(refine_mask 가 금지 구역·GrabCut 옵션 수용), `segmentation.py`(others, SEG_IMGSZ/SEG_NMS_IOU), `video_processor.py`, `workflows/{graph,nodes,state}.py`, 관련 테스트

### 3.3 기술 포인트
- 소유권 규칙: 대상 인스턴스에서 다른 인스턴스 몫을 덜어내되 원래 면적의 50% 미만이 되면(MIN_KEEP) 덜어내지 않는 안전장치, 작은 섬 제거
- 정답 없이 알 수 있는 위험 신호 `meta.leak` 기록(후속 커밋에서 상관 분석)

### 3.4 의도적으로 하지 않은 것
- 입력 크기 확대·NMS·신뢰도 조정·더 큰 YOLO: 측정상 이득 없음/역효과라 기본값 불변(옵션만 유지)
- 문장 해석 쪽 개선은 후속 커밋

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 pytest 330 통과
- 대표 결과(개별 라운드): GrabCut 끔 경계 F 0.52→0.61, CLAHE 끔 선택 정확 0.89→0.91·섞임 6.3→5.4% (조합 효과와 신뢰구간은 검증 문서)

### 4.2 부작용 / 리스크
- 모델 수준 오선택(미검출·합쳐진 사람) 약 10% 와 섞임 5% 초과 사진 약 11% 는 남음
- GrabCut 을 끄면 경계가 약간 단순해질 수 있음(경계 F 는 오히려 개선)

### 4.3 후속 작업
- 문장 해석(키워드 파서·체인) 보강, 검증 문서 정리

### 4.4 관련 문서
- `docs/vaildates/leak-diagnosis-20261008.md`

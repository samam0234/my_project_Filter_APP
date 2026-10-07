# 건물·하늘·도로 같은 배경 덩어리를 SegFormer(ADE20K, ONNX)로 인식 / `594d7c9b3c4c081847ae3db18e9a0675916f60c1`

> 브랜치: `feature/stuff-segmentation`  
> 작성일: `2026-10-08 04:19`  
> 작성자: `agent`  
> 파일명: `261008_0419_594d7c9_stuff-segformer-onnx_feature-stuff-segmentation.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(segmentation): 건물·하늘·도로 같은 배경 덩어리를 SegFormer(ADE20K, ONNX)로 인식` |
| **커밋 번호 (SHA)** | `594d7c9b3c4c081847ae3db18e9a0675916f60c1` |
| **짧은 SHA** | `594d7c9` |
| **브랜치** | `feature/stuff-segmentation` |
| **부모 커밋** | `1672f4f` |

## 2. 주 커밋 내용

- `backend/app/services/stuff_segmentation.py`: SegFormer(ADE20K) ONNX 로 건물·하늘·도로·인도·나무·잔디·물·산·벽·바닥·천장·땅·다리·울타리 14개 묶음 세그
- `scripts/export_stuff_onnx.py` (모델 내보내기·검증), `scripts/experiments/stuff_seg_compare.py` (b0·b2·b5 비교)
- `Segmentor` 연결: 덩어리 대상 → SegFormer, 낱개와 섞이면 YOLO+SegFormer 합집합, 모델 없으면 기존 흐름
- 어휘: `prompt_spec.STUFF_GROUPS` · 한국어/영어 별칭 · LLM 지시문·예시, 휴리스틱 파서 키워드
- 설정 `STUFF_SEG_ENABLED` · `STUFF_MODEL_PATH` · `STUFF_MIN_PROB` · `STUFF_USE_GPU`, 기동 워밍업, 콘솔 시스템 화면
- 프론트: 한글 라벨·피드백 후보·가이드 문구(낡은 "5종" 정정), 테스트 29건

## 3. 상세 내용

### 3.1 배경 / 목적
사용자: "건물 인식은 못 하는 것 같은데 학습해야 하는 것 아냐?" → 학습 대신 사전학습 의미 분할(2번안)을 선택.

### 3.2 변경 범위
- 추가: `backend/app/services/stuff_segmentation.py`, `scripts/export_stuff_onnx.py`, `scripts/experiments/stuff_seg_compare.py`, `tests/unit/test_stuff_segmentation.py`,
  `docs/vaildates/stuff-segmentation-20261008.md` · `stuff_seg_compare_20261008.json` · 그림 2장
- 수정: `backend/app/{core/config,main}.py`, `backend/app/services/{prompt_spec,segmentation,system_status}.py`, `backend/app/workflows/nodes.py`,
  `console/src/{pages/SystemPage(.test).tsx, types/index.ts}`, `frontend/src/{components/feedback/FeedbackPanel,pages/GuidePage}.tsx`, `frontend/src/utils/formatters(.test).ts`,
  `.env.example`, `backend/models/README.md`, `docs/API_DOCUMENTATION.md`, `docs/vaildates/README.md`, `tests/unit/test_access.py`

### 3.3 기술 포인트
- 묶음 확률 = 소속 클래스 확률의 **합** (저해상도 softmax → 합 → 선형 확대 → 0.5). building/house/skyscraper 사이에서 표가 갈려 건물이 구멍 나는 것을 막는다. 단위 테스트로 고정
- 연결 성분(면적 0.3% 이상, 최대 24개)을 인스턴스로 → 기존 `instance_selector` 가 위치·크기·색 선택에 그대로 사용
- 모델 선택: ADE20K 검증 100장, 건물 IoU b0 0.849 · b2 0.861 · b5 0.848 (표본 오차 범위), 묶음 평균 0.659 · 0.701 · 0.713, CPU 108 · 480 · 1,094ms → b2 기본, b0 는 설정으로 교체 가능
- 모델 파일(.onnx, 110MB)은 git 무시(`backend/models/*`) — Docker 는 볼륨 마운트로 받는다
- **잘못 알고 있던 것 정정**: 사용자 가이드가 "5종만 압니다"라고 적었으나 이미 COCO 80종이었다

### 3.4 의도적으로 하지 않은 것
- 새로 학습 / 미세 조정 (사전학습만으로 건물 IoU 0.86 — 필요성은 측정으로 확인 후)
- 큰 영역 지우기용 인페인팅 교체(LaMa), LoRA 파서 재학습

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 317, 프론트 vitest 44 · build, 콘솔 vitest 21 통과
- [x] Docker 재빌드 후 실제 요청 4건: 건물/하늘/왼쪽 건물/건물 지우기 — 해석(LLM)·결과 모두 의도대로(지우기는 번짐)
- [ ] 실브라우저(Playwright) 흐름은 이번에 돌리지 않음

### 4.2 부작용 / 리스크
- 건물 크기 영역 지우기는 결과가 번져 보임 (가이드·문서에 명시)
- 땅(ground) IoU 0.25 · 울타리 0.48 은 약함
- LoRA 파서 사용 환경은 새 어휘를 모름 → 재학습 필요
- `.env` 에 CONSOLE_ADMINS 를 넣으면서 preflight 테스트가 흔들리던 것을 값 고정으로 수정

### 4.3 후속 작업
- 사용자 확인 후 병합, 큰 영역 지우기 개선

### 4.4 관련 문서
- `docs/vaildates/stuff-segmentation-20261008.md`

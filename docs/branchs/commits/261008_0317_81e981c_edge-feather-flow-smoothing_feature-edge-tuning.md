# 경계 정제 중복 제거·경계 안티앨리어싱·영상 흐름 보정 스무딩 / `81e981c3af6a6c226d680c0ea03c39c65d508ade`

> 브랜치: `feature/edge-tuning`  
> 작성일: `2026-10-08 03:17`  
> 작성자: `agent`  
> 파일명: `261008_0317_81e981c_edge-feather-flow-smoothing_feature-edge-tuning.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `perf(effects): 경계 정제 중복 제거·경계 안티앨리어싱·영상 흐름 보정 스무딩` |
| **커밋 번호 (SHA)** | `81e981c3af6a6c226d680c0ea03c39c65d508ade` |
| **짧은 SHA** | `81e981c` |
| **브랜치** | `feature/edge-tuning` |
| **부모 커밋** | `ed6a597` |

## 2. 주 커밋 내용

- 사진: GrabCut 정제 **2번 → 1번** (`apply_effects(refine=False)`), 마스크 확대 최근접 → 선형+임계(`upscale_mask`)
- 블러·배경 제거 경계를 **가우시안 안티앨리어싱 알파**로 합성 (`feather_alpha`, 블러는 알파 블렌딩)
- 영상: **광학 흐름 보정 시간축 스무딩** `TemporalSmoother` (flow · ema), 설정 `VIDEO_TEMPORAL_SMOOTHING` · `VIDEO_SMOOTHING_WEIGHT`
- 실험 `scripts/experiments/edge_quality.py`, 결과 `docs/vaildates/edge-tuning-20261008.md` · `edge_quality_20261008.json` · 비교 그림 2장
- 테스트 `tests/unit/test_edge_tuning.py` 10건

## 3. 상세 내용

### 3.1 배경 / 목적
사용자: "배경 제거는 잘 되는데 튜닝 좀만 하면 더 잘 될 것 같다" → 제안한 순서(① 경계 ② 영상 흔들림)대로, 측정 먼저.

### 3.2 변경 범위
- 수정: `backend/app/services/{effects,video_processor}.py`, `backend/app/workflows/nodes.py`, `backend/app/routers/video.py`, `backend/app/core/config.py`, `.env.example`, `docs/vaildates/README.md`
- 추가: `scripts/experiments/edge_quality.py`, `tests/unit/test_edge_tuning.py`, `docs/vaildates/edge-tuning-20261008.md` · `edge_quality_20261008.json` · 그림 2장

### 3.3 기술 포인트
- 측정: COCO 사람 150장(+3배 확대본), 정답 폴리곤 대비 IoU · 경계 F(DAVIS, 허용 0.4% 대각선). 영상은 이동·재압축·잡음 클립 30개, 흔들림 = 1 − IoU(현재, 알려진 이동으로 옮긴 이전)
- 결과: 정제 1번으로 경계 F 0.406→0.506, IoU 0.760→0.789, 시간 1.18s→0.62s (3배: 0.419→0.478, 2.81s→1.51s)
- 영상: 흐름 보정 0.3 → 흔들림 0.0712→0.0357, IoU 0.805→0.811, 10ms/프레임. 그냥 섞기는 꼬리로 IoU 0.782
- **버린 것**: 넓은 가이드 필터 경계 — 잔디 같은 배경을 끌어와 번짐 띠(그림으로 확인, soft IoU −0.011). 가우시안 1.5px 로 교체(−0.003)
- **실수와 수정**: 첫 스무딩 구현은 현재 비중 0.6 — 이진 마스크라 임계를 항상 현재 프레임이 정해 효과 0 (세 방식 수치가 똑같아 발견). 비중 < 0.5 를 설정 검증으로 강제
- 선형 확대는 GrabCut 뒤에는 수치 차이가 없다 — 정제 없는 경로 보호용으로 유지한다고 문서에 명시

### 3.4 의도적으로 하지 않은 것
- 영상 프레임마다 GrabCut 을 빼는 속도 튜닝, SAM2 정밀화 — 문서 6절 후보로

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 288 통과 (신규 10)
- [x] 실험 2회: 사진 비교 수치(current/once/linear) 두 번 동일하게 재현
- [x] 실제 영상 경로: 스무딩 켜고 끈 처리 시간 차이 오차 범위 (30프레임 약 30s)

### 4.2 부작용 / 리스크
- 배경 제거 PNG 의 알파 경계가 0/255 가 아니라 1~2px 중간값 — 합성 프로그램에서 더 자연스럽지만 "딱 잘린" 결과를 기대하던 사용자에겐 다름
- 스무딩은 빠르게 움직이는 대상에서 흐름 추정이 틀리면 한 프레임 늦을 수 있음 (합성 클립 기준으로는 정확도 상승)

### 4.3 후속 작업
- 실브라우저 확인 · Docker 재빌드 · 사용자 확인 후 병합

### 4.4 관련 문서
- `docs/vaildates/edge-tuning-20261008.md`

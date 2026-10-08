# 영상·경계·배경 덩어리·객체 섞임 작업 4개 브랜치 총 병합 / `7c65b87`

> 브랜치: `develop`  
> 작성일: `2026-10-08`  
> 작성자: `agent`  
> 파일명: `261008_1451_7c65b87_merge-video-edge-stuff-leak_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge(develop): 영상·경계·배경 덩어리·객체 섞임 작업 4개 브랜치 총 병합` |
| **병합 커밋 (쌓인 순서)** | `b04c98e` video-fixes → `2f83f89` edge-tuning → `b7793ce` stuff-segmentation → `7c65b87` leak-diagnosis |
| **브랜치** | `develop` (`git merge --no-ff`, 사용자 지시 "마저 못한 작업 마무리 후 최종 병합"에 따라 마지막에 한 번) |
| **병합 전 develop** | `b4be99c` |

## 2. 주 커밋 내용

| 브랜치 | 커밋 | 내용 |
|--------|------|------|
| `feature/video-fixes` | `8ae8528` · `920362d` | 영상 결과 H.264 mp4 복귀, 큰 영상 블러 세기 보정, 결과를 브라우저(IndexedDB)에 보관해 다시 재생·저장 |
| `feature/edge-tuning` | `81e981c` | 경계 정제 중복 제거·안티앨리어싱·영상 흐름 보정 스무딩 |
| `feature/stuff-segmentation` | `594d7c9` | 건물·하늘·도로 등 배경 덩어리를 SegFormer(ADE20K, ONNX)로 인식 |
| `feature/leak-diagnosis` | `03eb969` · `805f6d9` · `fe8d736` · `c806f1d` · `deae8b2` | 지정하지 않은 객체가 섞여 안 지워지는 문제: 정답 주석 107개 사진 라운드로 원인 규명, 겹침 덜어내기·GrabCut/CLAHE 끔 기본값, 키워드 파서 역할 규칙, LangChain 해석 체인(기본), LangGraph 어려운 사례 수집, LoRA 방해물 시드·평가셋 |

## 3. 상세 내용

### 3.1 배경 / 목적
영상 재생·다운로드 블러 문제, 경계 품질, 건물 인식, 그리고 "LLM 이 특정 대상을 가리켜도 언급 안 된 인물·동물·물체가 합쳐져 안 지워지는" 문제를 해결하고 RAG·LangGraph·LangChain·LoRA 에 새 학습 내용이 반영되는 경로를 정리했다.

### 3.2 변경 범위
각 브랜치 커밋 기록 참조 (`docs/branchs/commits/*_feature-video-fixes.md` … `*_feature-leak-diagnosis.md`).

### 3.3 기술 포인트
- 충돌 없음. 브랜치가 쌓인 구조라 병합 결과 트리 = `feature/leak-diagnosis` 트리 (diff 0)
- 기본값 변경: `MASK_EXCLUSIVE=subtract`, `MASK_GRABCUT=false`, `PREPROCESS_CLAHE=false`, `PROMPT_CHAIN=langchain`, `PROMPT_VOTES=3`

### 3.4 의도적으로 하지 않은 것
- main 병합 · push · 배포, LoRA 재학습 실행, 세그 모델(YOLO) 재학습

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 병합 후 백엔드 pytest 371 passed, 프론트 vitest 44 · build, 콘솔 vitest 21 · build 통과
- [x] Docker 실제 업로드 API 52장(정답 주석 대비): 대상 해석 52/52 정확
  - 가장 왼쪽 사람 24장: 섞임 7.5%(5% 초과 17%) · IoU 0.782
  - 강아지만 14장: 섞임 2.9% · IoU 0.867 (2장은 검출 실패로 투명 결과 없음)
  - 사람만 14장: 섞임 2.1% · IoU 0.865

### 4.2 부작용 / 리스크
- 병합 직전 Docker 서비스 DB(`backend/data/cutnkeep.db`, SQLite)의 `jobs` 루트 페이지가 OpenCV 경고 텍스트로 덮여 손상됨 → 읽을 수 있는 `admin` 계정·세션만 새 DB 로 옮겨 복구. 손상본은 `backend/data/cutnkeep.corrupt-20261008.db` 로 보존(git 무시). 작업 기록 25건 유실(보존 기한 대부분 지남). 원인 프로세스는 미확정 — 호스트 백엔드와 Docker 백엔드가 같은 DB 파일을 번갈아 쓴 시간대에 발생
- 모델 수준 오선택 약 10%·5% 초과 섞임 약 11% 는 남음 (세그 재학습 필요)
- origin 에는 push 하지 않음

### 4.3 후속 작업
- LoRA 재학습(`python scripts/retrain_lora.py --force`), 어려운 사례 수집(`HARD_EXAMPLE_CONF`) 켤지 결정, 호스트/Docker 서비스 DB 분리
- 테스트 회원 `fin9f6f1868` 콘솔에서 삭제

### 4.4 관련 문서
- `docs/vaildates/leak-diagnosis-20261008.md`, `docs/guidance/learning-loop.md`

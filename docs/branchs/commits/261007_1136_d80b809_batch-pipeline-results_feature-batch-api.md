# 배치·영상이 단일 업로드와 같은 파이프라인을 타고 결과를 받을 수 있게 / `d80b809ff1523f231d31197a3047d43e647397f1`

> 브랜치: `feature/batch-api`  
> 작성일: `2026-10-07 11:36`  
> 작성자: `agent`  
> 파일명: `261007_1136_d80b809_batch-pipeline-results_feature-batch-api.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(batch): 배치·영상이 단일 업로드와 같은 파이프라인을 타고 결과를 받을 수 있게` |
| **커밋 번호 (SHA)** | `d80b809ff1523f231d31197a3047d43e647397f1` |
| **짧은 SHA** | `d80b809` |
| **브랜치** | `feature/batch-api` |
| **부모 커밋** | `15d96d7` (develop) |

## 2. 주 커밋 내용

- 배치 워커 → `run_pipeline` (인스턴스 선택·원본 크기 복원·재시도 포함)
- 배치 결과 서빙: 내 배치 목록 · 항목별 원본/결과 이미지 · zip 다운로드 (본인만)
- 영상: 프레임마다 selector, 공용 세그 모델, CORS 헤더 노출
- 업로드 검증에 이미지 시그니처 검사

## 3. 상세 내용

### 3.1 배경 / 목적

인수인계(Grok) "배치와 영상은 API만 있습니다. 프론트·콘솔 화면은 없습니다"를 받아 화면을 만들기 전에 API 를 점검했다.
화면에 붙이려 보니 API 가 쓸 수 있는 상태가 아니었다.

### 3.2 발견한 문제 (인수인계 코드 점검)

| 문제 | 영향 |
|------|------|
| 배치가 `ImageProcessor.run` 사용 → `selector` 미적용 | 배치에서 "왼쪽에서 두 번째 사람 지워줘" 가 **사람 전체를 지움** (핵심 기능 누락) |
| 마스크를 원본 크기로 복원하지 않음, 재시도 없음 | 1280px 넘는 사진에서 마스크·원본 크기 불일치, 단일 업로드와 결과 달라짐 |
| 배치 결과 이미지를 내려받는 API 없음 | `out/0000.jpg` 경로만 응답, 서빙 라우트 없음 → 화면에서 결과를 볼 수 없음 |
| 배치·영상이 요청마다 `Segmentor` 를 새로 만듦 | 모델 반복 로드 (수 초 + GPU 메모리) |
| 영상도 `selector` 미적용 | 위와 같음 |
| 영상 응답 헤더가 CORS 에 노출 안 됨 | 프론트가 다른 도메인(Vercel 등)이면 프레임 수 헤더를 못 읽음 |
| 업로드 검증이 클라이언트가 보낸 MIME 만 믿음 | 평문 텍스트도 `image/jpeg` 로 통과, 배치 중간에 터짐 |
| `ImageProcessor.run` 자체는 그대로 둠 | 다른 호출처 없음 확인 (배치 전용이었음) — 이후 정리 후보 |

### 3.3 변경 범위

- 수정: `backend/app/{tasks/batch_tasks.py, routers/{batch,video}.py, services/video_processor.py, workflows/{graph,nodes}.py,
  repositories/batch_repository.py, core/security.py, main.py}`, `tests/unit/{test_phase2,test_security}.py`, `docs/API_DOCUMENTATION.md`
- 추가: `tests/unit/test_batch_api.py`

### 3.4 기술 포인트

- `run_pipeline(..., parsed=)`: 미리 해석된 프롬프트를 넘기면 `prompt_analyzer` 가 LLM 을 건너뜀 → 배치 50장이어도 해석 1회
- 배치 항목 결과는 파이프라인 임시 폴더에서 `batches/{id}/out/NNNN.png` 로 옮기고 임시 폴더 삭제
- 결과 이미지 라우트는 `Literal["before","after"]` + 경로가 배치 루트 안인지 확인 (경로 조작 방지), 남의 배치는 404
- 배치 실패 케이스는 학습 후보로 자동 저장하지 않음 (500장 등록이 학습 데이터 목록을 덮는 것 방지)

### 3.5 의도적으로 하지 않은 것

- 영상 프레임 간 추적(광학 흐름·LSTM) — 인수인계의 "큼" 항목, 별도 지시 필요
- 영상 mp4(H.264) 출력 — 환경별 코덱 제약으로 MJPG avi 유지 (브라우저 재생 불가, 다운로드 안내)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 배치: 왼쪽 사람만 남기는 요청에서 결과 알파가 왼쪽만 255, 오른쪽 0 (가짜 세그 2인)
- [x] 문장 해석 1회·세그 장당 1회, 중간 실패 항목이 뒤를 막지 않음 (ok·failed·ok)
- [x] zip 3장, 원본 바이트 그대로, 남의 배치 이미지·zip 404, 비로그인 401
- [x] 영상 요청이 `Segmentor.__init__` 을 부르면 테스트 실패 (공용 모델 사용 보장)
- [x] 시그니처: JPEG·PNG·WebP 통과, 빈 값·GIF·WAV(RIFF) 거절
- [x] pytest 전체 통과

### 4.2 부작용 / 리스크

- 이제 평문 텍스트 등을 `.jpg` 로 올리면 400 (이전엔 처리 중 실패). 정상 이미지에는 영향 없음
- 배치 결과·원본은 24시간 뒤 정리 스크립트가 지움 — 화면에 안내 필요

### 4.3 후속 작업

- 배치·영상 화면 (frontend · console), Celery 워커 실가동, 오픈보캐브 켜기

### 4.4 관련 문서

- `docs/API_DOCUMENTATION.md` (Batch · Video)

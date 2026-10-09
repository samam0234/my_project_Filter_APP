# 문서 전체를 현재 상태(보안 강화 · LaMa · GIF · 영상 작업 기록 · 디자인)에 맞게 갱신 / `8abdfaf4097ba824f804612d78ccc71583e34eb5`

> 브랜치: `feature/docs-refresh`  
> 작성일: `2026-10-09 05:16`  
> 작성자: `agent`  
> 파일명: `261009_0516_8abdfaf_docs-refresh_feature-docs-refresh.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 문서 전체를 현재 상태(보안 강화 · LaMa · GIF · 영상 작업 기록 · 디자인)에 맞게 갱신` |
| **커밋 번호 (SHA)** | `8abdfaf4097ba824f804612d78ccc71583e34eb5` |
| **짧은 SHA** | `8abdfaf` |
| **브랜치** | `feature/docs-refresh` |
| **부모 커밋** | `2a159c4` |

## 2. 주 커밋 내용

- 현재 상태를 설명하는 문서 25개를 최근 변경(보안 강화 · LaMa · GIF · 영상 작업 기록 · 해석 체인 · 디자인)에 맞게 갱신
- 루트 README 에 "할 수 있는 것" 표 · Docker 실행 · Phase 진행 상황
- 포트 설명을 127.0.0.1 바인딩 · 공개는 :80 · `BACKEND_PORT` 로 통일
- 자동 정리 · 자동 백업이 생겨 "cron 에 등록" 안내를 고침
- 테스트 · 모듈 · 실험 스크립트 목록과 개수를 실제와 맞춤

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 요청 "전체적으로 문서 업데이트". 최근 여러 브랜치(보안 · 품질 · 디자인 · 영상/GIF)가 병합되며 개요·가이드·설계 문서가 예전 사실(영상 webm, CLAHE·GrabCut 기본 켬, 콘솔 loopback 전용, cleanup cron, 테스트 16건 등)을 말하고 있었다.

### 3.2 변경 범위
- README · RUN · backend/frontend/console/scripts/tests README
- `docs/README.md`, `docs/WORKFLOW.md`, `docs/plan/{CURRENT_STACK,DATABASE,LOGIC_STRUCTURE,PROJECT_STRUCTURE,TESTING}.md`
- `docs/guidance/{user-frontend,console-admin,docker-run,api-usage,learning-loop}.md`, `docs/web_management/{ports-inventory,pre-deploy}.md`, `docs/Architecture/{apps,data-flow,docker-topology,overview}.md`

### 3.3 기술 포인트
- 충돌 시 `CURRENT_STACK.md` 를 우선하는 규칙에 맞춰 스냅샷부터 고치고 나머지를 맞춤

### 3.4 의도적으로 하지 않은 것
- 날짜가 박힌 기록(`docs/vaildates/*-YYYYMMDD.md` · `docs/branchs/commits` · `docs/find_debug`)은 당시 기록이라 그대로
- CI 의 Node 버전 등 코드·설정 변경 없음

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 문서 구조 테스트 포함 백엔드 pytest 405 통과

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 다음 기능 변경 때 `CURRENT_STACK.md` 의 "문서 갱신 시 체크" 목록부터 확인

### 4.4 관련 문서
- `docs/plan/CURRENT_STACK.md`

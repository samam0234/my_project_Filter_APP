# 시스템 화면 — 런타임·저장 공간·배포 점검과 보관 기간 정리 실행 / `16417795c5e13b442cc5fc6e30894540942d9ed2`

> 브랜치: `feature/console-system`  
> 작성일: `2026-10-07 21:30`  
> 작성자: `agent`  
> 파일명: `261007_2130_1641779_console-system-storage_feature-console-system.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(console): 시스템 화면 — 런타임·저장 공간·배포 점검과 보관 기간 정리 실행` |
| **커밋 번호 (SHA)** | `16417795c5e13b442cc5fc6e30894540942d9ed2` |
| **짧은 SHA** | `1641779` |
| **브랜치** | `feature/console-system` |
| **부모 커밋** | `5b871ce` |

## 2. 주 커밋 내용

- `GET /api/v1/console/system`: 런타임 스냅샷(`app/services/system_status.py`) — 모델을 새로 로드하지 않음
- `POST /api/v1/console/system/cleanup?dry_run=`: 보관 기간 지난 업로드 파일 정리
- 정리 로직 `app/services/retention.py` 로 이동, `scripts/cleanup.py` 가 같은 함수 사용 + `--dry-run`
- 콘솔 시스템 화면 재작성: 배포 점검(error 먼저) · 세그/오픈보캐브 · LLM/배치/영상/콘솔 설정 · 저장 공간 카드 · 미리 보기 → 정리

## 3. 상세 내용

### 3.1 배경 / 목적
시스템 화면은 `/health` 의 버전·DB 종류뿐이었다. 오픈 보캐브가 켜졌는지, 배치가 Celery 로 가는지(Redis 가 살아 있는지), 디스크가 얼마나 찼는지
운영자가 알 수 없었다. 실제로 로컬 `uploads/` 에 189시간 된 파일 33개(13.5MB)가 남아 있었다 — 정리 스크립트를 아무도 돌리지 않았다.

### 3.2 변경 범위
- 추가: `backend/app/services/{retention,system_status}.py`, `tests/unit/test_console_system.py`, `console/src/pages/SystemPage.test.tsx`
- 수정: `backend/app/routers/console.py`, `scripts/cleanup.py`, `console/src/{pages/SystemPage.tsx, api/client.ts, types/index.ts}`,
  `docs/guidance/console-admin.md`, `docs/API_DOCUMENTATION.md`

### 3.3 기술 포인트
- 세그 런타임은 `nodes._processor` 를 들여다보기만 함 (없으면 `not_loaded`) — 콘솔을 여는 것만으로 GPU 로드 금지 (테스트로 고정)
- Redis 는 `BATCH_USE_CELERY=true` 일 때만 1초 타임아웃 ping
- 저장 공간: `uploads/` 를 단일 작업(최상위 폴더들) · `batches/` · `videos/` 로 나눠 파일 수·용량·가장 오래된 나이·기간 지난 수
- "지금 정리" 버튼은 미리 보기로 대상이 1개 이상일 때만 활성화, 실행은 서버 로그에 `by=admin:{아이디}`
- 정리는 파일만 — DB 행(작업·배치 기록)은 유지 (사용자 화면은 이미지 대신 안내)

### 3.4 의도적으로 하지 않은 것
- 정리 자동 스케줄러(앱 내부 타이머) — 서버 cron 으로 `scripts/cleanup.py` 권장
- 만료된 작업 행 삭제

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 전체 통과 (신규 5건), 콘솔 vitest 21 · build 통과
- [x] 실제 저장소 스냅샷: jobs 32파일 14.2MB · 189.6시간, preflight 7건 / `scripts/cleanup.py --dry-run` → 33개 13.5MB 삭제 예정

### 4.2 부작용 / 리스크
- 큰 업로드 폴더는 스냅샷마다 전체 순회(파일 수에 비례) — 수만 개 이상이면 느려질 수 있음

### 4.3 후속 작업
- 오픈 보캐브 임계값 측정 문서(`feature/open-vocab-eval`), 실브라우저 점검, 총 병합

### 4.4 관련 문서
- `docs/guidance/console-admin.md` (시스템 · 저장 공간 정리 절), `docs/API_DOCUMENTATION.md`

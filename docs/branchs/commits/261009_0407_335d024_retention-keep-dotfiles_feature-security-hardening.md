# 자동 정리가 .gitkeep 같은 자리표시 파일을 지우지 않게, 지워진 uploads/.gitkeep 복구 / `335d024ac0c2669f80a214e5c4bc32668c34b123`

> 브랜치: `feature/security-hardening`  
> 작성일: `2026-10-09 04:07`  
> 작성자: `agent`  
> 파일명: `261009_0407_335d024_retention-keep-dotfiles_feature-security-hardening.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(security): 자동 정리가 .gitkeep 같은 자리표시 파일을 지우지 않게, 지워진 uploads/.gitkeep 복구` |
| **커밋 번호 (SHA)** | `335d024ac0c2669f80a214e5c4bc32668c34b123` |
| **짧은 SHA** | `335d024` |
| **브랜치** | `feature/security-hardening` |
| **부모 커밋** | `960bd8e` |

## 2. 주 커밋 내용

- `retention.cleanup_dir` 가 점(.)으로 시작하는 파일을 건너뛴다
- 앞 커밋(960bd8e)에 삭제로 들어간 `backend/data/uploads/.gitkeep` 복구
- 테스트 1건

## 3. 상세 내용

### 3.1 배경 / 목적
960bd8e 커밋에 `backend/data/uploads/.gitkeep` 삭제가 섞여 들어갔다.
**원인(커밋 후 확인)**: 사용자가 호스트에서 띄워 둔 `uvicorn app.main:app --reload`(2026-10-08 22:56 시작)가 백엔드 파일을 고칠 때마다
재시작했고, 새로 넣은 자동 정리가 기동 시 실제 `backend/data/uploads` 에서 24시간 지난 파일(`.gitkeep`)을 지웠다.
같은 시각들에 `backend/data/backups/cutnkeep.host-*.db` 백업이 생긴 것으로 확인. 커밋 메시지에는 "특정하지 못했다"고 적었으나 이후 밝혀짐.

### 3.2 변경 범위
- 수정: `backend/app/services/retention.py`, `tests/unit/test_security_hardening.py` · 복구: `backend/data/uploads/.gitkeep`

### 3.3 기술 포인트
- 자리표시 파일만 보호. 다른 실제 업로드는 정책대로 정리 (당시 실제 폴더 항목 수 53 유지 — 24시간이 안 된 것들)

### 3.4 의도적으로 하지 않은 것
- 호스트 개발 서버 중지 (사용자 프로세스)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 400 통과, 전체 실행 후 `.gitkeep` 유지

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 16dd40a: 테스트가 실제 업로드 폴더를 쓰지 않게

### 4.4 관련 문서
- `docs/guidance/security.md`

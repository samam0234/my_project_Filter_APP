# 현재 스택 기준으로 문서 전면 동기화 / `e7c3974`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-28 17:39`  
> 작성자: `while`  
> 파일명: `260728_1739_e7c3974_docs-current-stack-sync_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs: 현재 스택 기준으로 문서 전면 동기화` |
| **짧은 SHA** | `e7c3974` |
| **브랜치** | `feature/docs` |

## 2. 주 커밋 내용

- 신규 `docs/plan/CURRENT_STACK.md` — 포트·DB·Docker·제외 항목 스냅샷
- RUN / docker-run / docker-topology / ports-inventory 갱신 (Adminer 8081, MARIADB_PORT, Redis 6380)
- DATABASE · DEVELOPMENT 가이드 · PROJECT_STRUCTURE 반영
- MariaDB 비밀번호 전용·GSS/SSL 제외·requirements 루트·YOLO26s·training 링크
- 커밋 기록 경로 branchs/commits 재강조, mvp-checklist 갱신
- 루트 README 홈 vs `.github/Read_for_we` 구분

## 3. 제외·정리한 구 서술

- 고정 `localhost:3306` only / GSS MariaDB 이미지
- `backend/requirements*.txt` 존재 가정
- Compose 에 console 포함 오해

## 4. 후속

- develop `--no-ff` 병합·푸시

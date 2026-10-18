# data — 학습 공유 데이터 · DB 파일

> 백엔드가 **기록**하고 `training/` · `scripts/`가 **읽는** 학습 재료, 그리고 Docker MariaDB의 데이터 파일과 백업.

서비스 런타임 데이터(회원 업로드 · 호스트 SQLite)는 [`backend/data/`](../backend/data/README.md)에 있다.
**이 폴더의 내용은 Git에서 제외된다.** README와 폴더 유지용 `.gitkeep`만 추적한다.

## 구성

| 경로 | 쓰는 쪽 | 읽는 쪽 | 보관 |
|------|---------|---------|------|
| `feedback/` | 백엔드 `FeedbackService` — 좋아요 · 싫어요 · 정답 JSON · 파이프라인 실패 | `training/lora` · `scripts/pseudo_labeling.py` · `scripts/chroma_feedback.py` · 학습 DB 동기화 | 사이드카 JSON은 학습 루프용으로 유지. 실패 · 확신 낮은 요청 **사진**은 30일(`FEEDBACK_IMAGE_RETENTION_DAYS`), 계정 삭제 시 즉시 |
| `chroma/` | `scripts/chroma_feedback.py` (교정 · 좋아요만) | 백엔드 문장 해석이 확인된 예시를 더할 때 → [`chroma/README.md`](chroma/README.md) | 다시 만들 수 있음 |
| `pseudo_labels/` | `scripts/pseudo_labeling.py` | `training/lora` · YOLO 재학습 | Chroma에는 넣지 않음 |
| `mariaDB_datas/` | Docker MariaDB (bind mount → `/var/lib/mysql`) | MariaDB 컨테이너만 | **전체 ignore** — 비어 있는 채로 시작, `.gitkeep`도 두지 않는다 |
| `mariaDB_backups/` | `mariadb-backup` 서비스 — `<DB>-YYYYmmdd-HHMMSS.sql.gz` | 복구할 때 | 매일 · 7일 (같은 디스크) |
| `caddy/` | HTTPS 모드의 Caddy — 인증서 · 계정 키 | Caddy | 비밀 자료. 절대 커밋하지 않는다 |

## 피드백 파일

피드백 한 건은 `feedback/<id>.json`(사이드카 — `id`는 학습 DB `feedbacks`의 id)과, 필요하면 같은 이름의 `.jpg`(실패 · 확신 낮은 요청의 원본)다.
사이드카는 학습 DB(`feedbacks`)의 원본이기도 하다. 학습 DB가 꺼져 있다가 다시 켜지면 빠진 사이드카를 적재한다 (`LEARNING_SYNC_ON_START`).

- 좋아요 · 정답 알려주기는 콘솔에서 승인되어야 RAG 예시 · LoRA 학습에 들어간다.
- 피드백 1건에서 문장 샘플과 세그 샘플이 최대 2건 나온다 (`learning_samples`).
- 콘솔에서 삭제하면 사이드카까지 지운다.

## 설정 (저장소 루트 기준 상대 경로)

```env
FEEDBACK_DIR=data/feedback
PSEUDO_LABEL_DIR=data/pseudo_labels
FEEDBACK_IMAGE_RETENTION_DAYS=30
```

Docker Compose는 `./data/feedback` · `./data/pseudo_labels`를 컨테이너 `/app/data/feedback` · `/app/data/pseudo_labels`에, `./data/chroma`를 `/app/shared/chroma`(`PROMPT_CHROMA_SHARED_DIR`)에 마운트한다.

## MariaDB 파일

- `.env`의 계정 값(`MYSQL_*` · `MARIADB_*`)은 **이 폴더가 비어 있을 때 처음 한 번만** 적용된다.
- DB를 비우려면 `docker compose -p cut_and_keep down` 후 `data/mariaDB_datas/`를 지운다. bind mount라 `down -v`로는 지워지지 않는다.
- 컨테이너가 도는 중에 파일을 직접 건드리지 않는다.

자세히: [`docker/mariadb/README.md`](../docker/mariadb/README.md)

## 정책

- 비밀 · 개인 식별 원본을 장기 보관하지 않는다. 사진은 보관 기간이 지나면 지운다.
- 백업은 아직 **같은 서버 디스크**에만 있다. 서버 밖 백업은 남은 일이다.

## 관련 문서

- [`docs/plan/DATABASE.md`](../docs/plan/DATABASE.md)
- [`docs/guidance/learning-loop.md`](../docs/guidance/learning-loop.md)
- [`training/lora/README.md`](../training/lora/README.md)

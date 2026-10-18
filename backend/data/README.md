# backend/data — 서비스 런타임 데이터

> 백엔드가 요청을 처리하면서 만들고, **서비스 안에서만** 쓰는 데이터. 회원 업로드 · 호스트용 SQLite · 그 백업 · 승인 문장 벡터가 여기 있다.

학습 재료(피드백 · 의사 라벨 · 확인 피드백 Chroma · MariaDB 파일)는 여기가 아니라 루트 [`data/`](../../data/README.md)에 둔다.
**이 폴더의 내용은 전부 Git에서 제외된다.** `uploads/.gitkeep`과 이 README만 추적한다.

## 구성

| 경로 | 용도 | 수명 |
|------|------|------|
| `uploads/{job_id}/` | 회원 작업의 원본 · 결과 · 썸네일 · WebP. 영상은 `uploads/videos/` | `FILE_RETENTION_HOURS`(24) 뒤 **백엔드가 매시간 자동 삭제** (`FILE_CLEANUP_MINUTES`). 점(.)으로 시작하는 파일은 지우지 않는다 |
| `cutnkeep.host.db` | **호스트에서 띄운** 백엔드의 서비스 SQLite (`users` · `auth_*` · `signup_pending` · `jobs` · `batch_jobs`) | 영구 |
| `cutnkeep.db` | Docker 백엔드를 SQLite 모드(`DOCKER_DB_DIALECT=sqlite`)로 띄웠을 때의 서비스 DB. MariaDB로 바꾸면 기동 시 한 번 옮기고 파일은 남겨 둔다 | 영구 |
| `learning.db` | 학습 DB(MariaDB)가 꺼져 있을 때 잠시 쓰는 SQLite 대체 (`LEARNING_SQLITE_PATH`) | 다시 켜면 동기화 |
| `backups/` | 서비스 SQLite 백업 — 기동 직후 한 번 + `DB_BACKUP_HOURS`(24)마다 `{파일명}-YYYYmmdd-HHMMSS.db` | 최근 `DB_BACKUP_KEEP`(7)개 |
| `chroma/` | 승인된 문장 해석 예시의 Chroma (컬렉션 `approved_prompts`) → [`chroma/README.md`](chroma/README.md) | 승인 목록과 함께 다시 맞춤 |

비로그인 업로드는 이 폴더에 **남지 않는다.** 처리 결과는 data URL로 바로 돌려준다.

## 왜 SQLite 파일이 둘인가

호스트에서 직접 띄운 백엔드와 Docker 백엔드가 **같은 SQLite 파일을 쓰다가 손상된 적이 있다** (2026-10-08). SQLite는 한 파일을 한 프로세스씩 쓰는 구조라 두 프로세스가 동시에 쓰면 깨질 수 있다.

- 호스트 백엔드 → `cutnkeep.host.db` (`.env`의 `SQLITE_PATH`)
- Docker 백엔드 → 기본은 **MariaDB** (`DB_DIALECT=mariadb`). SQLite로 되돌리면 `cutnkeep.db`
- 백엔드는 서비스 SQLite 손상을 감지해 알린다. 2026-10-08에 손상된 파일은 복구 뒤 `cutnkeep.corrupt-20261008.db`로 남겨 두었다

SQLite 백업은 온라인 백업 API(`sqlite3.Connection.backup`)를 쓴다. 서비스가 쓰는 중에도 일관된 사본을 만든다 (파일 복사는 쓰는 중이면 깨질 수 있다).

## 설정 (backend/ 기준 상대 경로)

```env
UPLOAD_DIR=data/uploads
SQLITE_PATH=data/cutnkeep.host.db
LEARNING_SQLITE_PATH=data/learning.db
FILE_RETENTION_HOURS=24
FILE_CLEANUP_MINUTES=60
DB_BACKUP_HOURS=24
DB_BACKUP_KEEP=7
```

보관 기간을 바꾸면 개인정보 처리방침의 문구도 같이 바꾼다 (처리방침과 코드가 어긋난 적이 있다).

## Docker

Compose가 `./backend/data` → `/app/data`로 마운트한다. 학습 공유 폴더(`data/feedback` · `data/pseudo_labels` · `data/chroma`)는 루트 `data/`에서 따로 마운트된다.

## 다루는 법

- 서비스가 도는 중에 DB 파일을 직접 옮기거나 지우지 않는다.
- 테스트는 이 폴더를 건드리지 않는다 (임시 폴더 · 메모리 DB를 쓴다).
- 회원 삭제는 콘솔이나 `user_admin.delete_user`로 한다. 파일을 손으로 지우지 않는다.

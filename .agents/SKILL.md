---
name: cutnkeep-project
description: >
  Project rules for Cut & Keep (CutNKeep): architecture layers, dual DB,
  commit message language (English title / Korean body+footer), branchs commit
  log filenames, feature branch selection, console vs frontend. Use when coding,
  committing, documenting, or running Docker for this repo. Triggers: commit,
  branchs, console, backend layers, cut_and_keep.
---

# Cut & Keep Project Skill

## Project

- Name: 컷앤킵 / Cut & Keep  
- Repo root contains: `backend/`, `frontend/`, `console/`, `docs/`, `docker-compose.yml`  
- Phase 1 focus: single image pipeline, layered backend, SQLite local / MariaDB docker, ops console  

## Architecture (backend)

Allowed dependency direction:

```
routers → services/workflows → repositories → models
routers → schemas
```

- Do **not** put SQL in routers or OpenCV in repositories.  
- DB: `DB_DIALECT=sqlite|mariadb`, see `docs/plan/DATABASE.md`.  

## Apps

| Path | Role | Port |
|------|------|------|
| `frontend/` | End-user filter UI | 5173 |
| `console/` | Ops admin (jobs/health) | 5174 |
| `backend/` | API | 8000 |

## Git commits (mandatory language)

| Part | Language |
|------|----------|
| **Title (subject)** | **English only** — `type(scope): summary` |
| **Body** | **Korean** |
| **Footer** | **Korean** |

### Title rules

- Conventional Commits: `feat|fix|docs|chore|refactor|test|perf|ci|build`
- Scope examples: `backend`, `frontend`, `console`, `docker`, `docs`, `branchs`
- No trailing period; imperative mood (`add`, not `added`)

### Body / footer rules

- Explain what and why in Korean  
- Footer examples: `관련:`, `후속:`, `Breaking-Change:` (description in Korean)

### Full example

```
feat(docker): add cut_and_keep compose stack with slim backend image

Docker Compose 프로젝트명 cut_and_keep으로 스택을 구성함.
백엔드는 경량 requirements.docker.txt를 사용함.

관련: docs/Architecture/docker-topology.md
후속: console 서비스 compose 등록 검토
```

Full guide: `docs/guidance/commit-message.md`

## After commit — branchs log file

1. Copy structure from `docs/branchs/TEMPLATE.md`  
2. Filename **must** be:

```text
YY_MM_DD_[commitId]_[commitName]_[commitBranch].md
```

Example: `26_07_27_8914abe_backend-layers-db_feature-backend.md`  
- Year = last two digits  
- Branch slashes → hyphens  

3. Update table in `docs/branchs/README.md`

## Branch selection

Work on the matching `feature/*` branch, then merge to `develop`.  
See `docs/branchs/BRANCH_MAP.md`.

## Docker

- Project: `docker compose -p cut_and_keep ...`  
- Redis host port often `6380` (avoid 6379 clashes)  
- Images list is global in Docker Desktop — not a bug  

## Docs hub

When adding operational knowledge, put it in the right folder:

- `docs/Architecture/` · `docs/branchs/` · `docs/find_debug/`  
- `docs/guidance/` · `docs/trainings/` · `docs/repeater/`  
- `docs/vaildates/` · `docs/web_management/` · `docs/plan/`  

## Safety

- Never commit `.env` secrets  
- Do not force-push shared `main`/`develop` unless user asks  
- Prefer small, reviewable commits  

## Done criteria for code tasks

- Layers respected  
- Commit message language rules satisfied  
- branchs log file created when user expects documentation of the commit  

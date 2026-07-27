# Cut & Keep — Agent Instructions

You are working on **Cut & Keep** (`CutNKeep`): prompt-based selective background removal  
(FastAPI + React user app + React ops console + SQLite/MariaDB).

## Always read / follow

1. `.agents/SKILL.md` — full skill rules  
2. `docs/guidance/commit-message.md` — commit language rules  
3. `docs/branchs/TEMPLATE.md` — commit log file template  
4. `docs/plan/LOGIC_STRUCTURE.md` / `DATABASE.md` when touching backend  

## Commit message (mandatory)

```
Title: English only (Conventional Commits)
Body: Korean
Footer: Korean
```

Example:

```
feat(backend): add job list endpoint

Job 조회 API를 추가하고 콘솔에서 사용 가능하게 함.

관련: docs/guidance/console-admin.md
```

## After every commit

Create `docs/branchs/commits/YY_MM_DD_[sha]_[name]_[branch].md` using the template.  
Branch `/` → `-` in filenames (`feature/docs` → `feature-docs`).

## Prefer correct git branch

| Work | Branch |
|------|--------|
| API, DB, layers | `feature/backend` |
| User UI | `feature/frontend` |
| Ops console / docs hub | `feature/docs` |
| OpenCV | `feature/opencv` |
| YOLO | `feature/yolo` |

Integrate via `develop`. Do not force-push `main` without release process.

## Stack map

- `backend/` — FastAPI, routers, schemas, repositories, models, db  
- `frontend/` — user app :5173  
- `console/` — ops console :5174  
- Docker project name: `cut_and_keep`

# GitHub Copilot — Cut & Keep

This file guides Copilot Chat / coding agent in this repo.

## Project

Cut & Keep: prompt-based background removal.  
`backend` FastAPI, `frontend` user UI (:5173), `console` ops UI (:5174).

## Commit messages (required)

When suggesting or creating commits:

```
type(scope): English summary

한국어로 본문 작성

한국어로 바닥글 작성 (선택)
```

- Title must **not** contain Hangul.  
- Body and footer must be Korean.  
- Details: `docs/guidance/commit-message.md`

## Architecture

Routers → services/workflows → repositories → models.  
Schemas are Pydantic DTOs only.

## Docs after commits

`docs/branchs/commits/YY_MM_DD_[id]_[name]_[branch].md`  
Template: `docs/branchs/TEMPLATE.md`

## Full skill

`.agents/SKILL.md`

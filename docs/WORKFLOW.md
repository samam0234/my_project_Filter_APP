# LangGraph Workflow

정본은 [plan/LOGIC_STRUCTURE.md](plan/LOGIC_STRUCTURE.md) §3–4.

```
prompt_analyzer → preprocessor → segmentor → validator
       ├─ ok → effect_applier → END
       ├─ fallback (retry) → segmentor
       └─ fail → feedback_collector → effect_applier → END
```

코드: `backend/app/workflows/`

# System Overview

## 한 줄

프롬프트 기반 선택적 배경 제거(Cut & Keep) — React 사용자 앱 + 운영 콘솔 + FastAPI + SQLite/MariaDB.

## 구성 요소

```
[Browser]
   │
   ├─ frontend :5173  사용자 업로드/필터
   └─ console  :5174  운영 Job/헬스 모니터링
         │
         ▼
   backend :8000  FastAPI
         │
         ├─ LangGraph workflow + OpenCV/YOLO(or stub)
         ├─ Repository → SQLite | MariaDB
         └─ Files: data/uploads, data/feedback
```

## Phase

| Phase | 초점 |
|-------|------|
| 1 (현재) | 단일 이미지, 계층 구조, DB, Docker, Console |
| 2 | SAM2, 배치 500, LoRA |
| 3 | 영상, Temporal Smoothing, 고도 배포 |

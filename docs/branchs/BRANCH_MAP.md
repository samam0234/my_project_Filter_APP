# Branch Map

근거: `docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md`  
병합 상세: `docs/guidance/branch-merge.md`

```
main                 ← 배포 통합 라인 (일자로 붙이는 곳 ②)
│
└── develop          ← 개발 통합 라인 (일자로 붙이는 곳 ①)
      │
      ├── feature/*  ← 여기서만 일상 작업·커밋
      ├── bugfix/*
      └── experimental/*
```

## 규칙 요약 (필수)

| 항목 | 규칙 |
|------|------|
| **작업** | 각자 `feature/*` (등) 브랜치에서 커밋 |
| **일자 병합 / 통합** | **`develop` 또는 `main` 에만** 붙인다 |
| **feature 완료 시** | **`develop` 에 merge** (feature끼리 장기 통합 금지) |
| **배포** | `release/*` 검증 후 **`main`** |
| **커밋 메시지** | 제목 영어 / 본문·바닥글 한국어 |
| **커밋 후 기록** | `docs/branchs/commits/YY_MM_DD_[id]_[name]_[branch].md` |

### 한 줄

> 작업은 갈라진 feature 에서, **합칠 때만 develop·main 일자 라인에 붙인다.**

## 현재 주요 feature

| 브랜치 | 용도 |
|--------|------|
| `feature/backend` | API, DB, 계층, Docker |
| `feature/docs` | 문서 허브, console, 에이전트 스킬 |
| `feature/frontend` | 사용자 React 앱 |
| `feature/opencv` | OpenCV 파이프라인 |
| `feature/yolo` | YOLO-seg |
| … | 계획서 표 참고 |

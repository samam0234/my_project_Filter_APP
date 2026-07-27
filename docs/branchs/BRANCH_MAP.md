# Branch Map

근거: `docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md`

```
main
└── develop          ← 통합 개발 (원격 origin/develop 푸시됨)
    ├── feature/backend   (스키마·라우터·레포·DB·Docker 작업 반영)
    ├── feature/docs      (문서 허브 + console 등)
    ├── feature/frontend
    ├── feature/opencv
    ├── feature/yolo
    └── …
```

## 규칙 요약

- 일상 작업: `feature/*` → `develop` merge
- 배포: `release/*` → `main`
- 커밋 메시지: 제목 영어 / 본문 한국어
- 커밋 후: `docs/branchs/commits/` 에 템플릿 기록

# branchs — 브랜치 · 커밋 기록

기능 브랜치와 커밋 이력을 **템플릿에 맞춰** 남기는 폴더입니다.  
한 줄 요약만 적는 것은 금지합니다.

## Git 커밋 메시지 (필수)

| 제목 | 본문 | 바닥글 |
|------|------|--------|
| **영어** | **한국어** | **한국어** |

→ [`docs/guidance/commit-message.md`](../guidance/commit-message.md)

## 브랜치 · 병합 (필수)

| 작업 | 통합(일자 병합) |
|------|-----------------|
| `feature/*` 등에서 커밋 | **`develop` / `main` 에만** merge로 붙임 |

→ [`docs/guidance/branch-merge.md`](../guidance/branch-merge.md) · [`BRANCH_MAP.md`](./BRANCH_MAP.md)

## 필수 문서


| 파일 | 설명 |
|------|------|
| [TEMPLATE.md](./TEMPLATE.md) | **커밋 기록 작성 템플릿 (필수 준수)** |
| [BRANCH_MAP.md](./BRANCH_MAP.md) | 브랜치 전략 요약 |
| [commits/](./commits/) | 커밋별 상세 기록 파일 |

## 파일명 규칙 (commits/)

```text
YY_MM_DD_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

예: `26_07_27_8914abe_backend-layers-db_feature-backend.md`

- 연도 **뒤 2자리** + 월 + 일 (언더스코어 구분)
- 브랜치명의 `/` 는 `-` 로 치환 (`feature/backend` → `feature-backend`)
- 상세: [TEMPLATE.md](./TEMPLATE.md)

## 작성 절차

1. 커밋 완료 후 `TEMPLATE.md`를 복사한다.
2. 위 파일명 규칙으로 `commits/` 에 저장한다.
3. 제목/커밋 번호 · 주 내용 · 상세 · 결과 4섹션을 채운다.
4. 이 README 표에 링크를 추가한다.

## 기록 목록

| 커밋 | 제목 | 파일 |
|------|------|------|
| `4b1e6ad` | initial project scaffold | [commits/26_07_27_4b1e6ad_initial-scaffold_main.md](./commits/26_07_27_4b1e6ad_initial-scaffold_main.md) |
| `1342117` | ignore TypeScript build info | [commits/26_07_27_1342117_ignore-tsbuildinfo_develop.md](./commits/26_07_27_1342117_ignore-tsbuildinfo_develop.md) |
| `8914abe` | schema/router/repo + dual DB | [commits/26_07_27_8914abe_backend-layers-db_feature-backend.md](./commits/26_07_27_8914abe_backend-layers-db_feature-backend.md) |
| `8157388` | cut_and_keep docker stack | [commits/26_07_27_8157388_docker-cut-and-keep_feature-backend.md](./commits/26_07_27_8157388_docker-cut-and-keep_feature-backend.md) |
| `5420cfb` | console + docs hub | [commits/26_07_27_5420cfb_console-and-docs-hub_feature-docs.md](./commits/26_07_27_5420cfb_console-and-docs-hub_feature-docs.md) |
| `4ccdc4d` | agents + commit guide | [commits/26_07_27_4ccdc4d_agents-commit-guide_feature-docs.md](./commits/26_07_27_4ccdc4d_agents-commit-guide_feature-docs.md) |
| `2b22d75` | branch-merge guide | [commits/26_07_27_2b22d75_branch-merge-guide_feature-docs.md](./commits/26_07_27_2b22d75_branch-merge-guide_feature-docs.md) |
| `2d2a2df` | agents 한국어화 | [commits/26_07_27_2d2a2df_agents-korean_feature-docs.md](./commits/26_07_27_2d2a2df_agents-korean_feature-docs.md) |
| `a49e922` | RUN.md + Scribble | [commits/26_07_27_a49e922_run-scribble_feature-docs.md](./commits/26_07_27_a49e922_run-scribble_feature-docs.md) |

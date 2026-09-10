# branchs — 브랜치 · 커밋 기록

기능 브랜치와 커밋 이력을 **템플릿에 맞춰** 남기는 폴더입니다.  
한 줄 요약만 적는 것은 금지합니다.

## 당부 (에이전트 · 사람 · 예외 없음)

| 규칙 | 내용 |
|------|------|
| **경로** | **`docs/branchs/commits/` 만** 사용 |
| **금지 경로** | `docs/commits/` 등 다른 폴더에 기록하지 말 것 |
| **시점** | **커밋을 하거나 하기 전** 무조건 md 작성 |
| **생략** | “작다 / 나중에 / 푸시만” → **금지** |
| **템플릿** | [TEMPLATE.md](./TEMPLATE.md) 필수 준수 |
| **파일명** | `YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md` |

커밋·푸시 워크플로 예:

1. 코드 변경  
2. **`docs/branchs/commits/….md` 작성** (또는 커밋 직후 SHA 넣고 작성)  
3. `git commit` (기능)  
4. 기록 파일 커밋 (`docs(branchs): …`)  
5. push / develop 병합

## Git 커밋 메시지 (필수)

| type/scope | 제목 요약 | 본문 | 바닥글 |
|------------|-----------|------|--------|
| **영어** | **한국어** | **한국어** | **한국어** |

예: `feat(tts): 음성 인식 추가` ✅ · `feat(llm): add to engine` ❌  

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
YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

예: `260727_1446_5420cfb_console-and-docs-hub_feature-docs.md`

| 조각 | 의미 |
|------|------|
| `260727` | 날짜 (년2+월+일, 구분자 없음) |
| `1446` | **시분** (14:46) |
| 이후 | 커밋 ID · 이름 · 브랜치 (기존과 동일) |

- 브랜치 `/` → `-`  
- 상세: [TEMPLATE.md](./TEMPLATE.md)

## 작성 절차

1. 커밋 완료 후 `TEMPLATE.md`를 복사한다.
2. 위 파일명 규칙으로 `commits/` 에 저장한다. (`git log -1 --format=%ci` 로 시분 확인)
3. 제목/커밋 번호 · 주 내용 · 상세 · 결과 4섹션을 채운다.
4. 이 README 표에 링크를 추가한다.

## 기록 목록

| 커밋 | 제목 | 파일 |
|------|------|------|
| `90a56e8` | feature/lora → develop 병합 (no-ff) | [commits/260910_1612_90a56e8_merge-lora_develop.md](./commits/260910_1612_90a56e8_merge-lora_develop.md) |
| `db607ed` | LoRA 학습 루프 의존성 가드·출력 디렉터리 | [commits/260814_0155_db607ed_lora-deps-output-dir_feature-lora.md](./commits/260814_0155_db607ed_lora-deps-output-dir_feature-lora.md) |
| `2db7501` | YOLO26s 기본 비전 모델 통일 | [commits/260728_1013_2db7501_yolo26s-default-and-manual-comments_feature-backend.md](./commits/260728_1013_2db7501_yolo26s-default-and-manual-comments_feature-backend.md) |
| `af3ed90` | 한글 주석 보강 및 requirements 루트 이전 | [commits/260728_0914_af3ed90_korean-comments-requirements-root_feature-backend.md](./commits/260728_0914_af3ed90_korean-comments-requirements-root_feature-backend.md) |
| `4b1e6ad` | initial project scaffold | [commits/260727_1207_4b1e6ad_initial-scaffold_main.md](./commits/260727_1207_4b1e6ad_initial-scaffold_main.md) |
| `1342117` | ignore TypeScript build info | [commits/260727_1207_1342117_ignore-tsbuildinfo_develop.md](./commits/260727_1207_1342117_ignore-tsbuildinfo_develop.md) |
| `8914abe` | schema/router/repo + dual DB | [commits/260727_1220_8914abe_backend-layers-db_feature-backend.md](./commits/260727_1220_8914abe_backend-layers-db_feature-backend.md) |
| `8157388` | cut_and_keep docker stack | [commits/260727_1303_8157388_docker-cut-and-keep_feature-backend.md](./commits/260727_1303_8157388_docker-cut-and-keep_feature-backend.md) |
| `5420cfb` | console + docs hub | [commits/260727_1446_5420cfb_console-and-docs-hub_feature-docs.md](./commits/260727_1446_5420cfb_console-and-docs-hub_feature-docs.md) |
| `4ccdc4d` | agents + commit guide | [commits/260727_1456_4ccdc4d_agents-commit-guide_feature-docs.md](./commits/260727_1456_4ccdc4d_agents-commit-guide_feature-docs.md) |
| `2b22d75` | branch-merge guide | [commits/260727_1502_2b22d75_branch-merge-guide_feature-docs.md](./commits/260727_1502_2b22d75_branch-merge-guide_feature-docs.md) |
| `2d2a2df` | agents 한국어화 | [commits/260727_1505_2d2a2df_agents-korean_feature-docs.md](./commits/260727_1505_2d2a2df_agents-korean_feature-docs.md) |
| `a49e922` | RUN.md + Scribble | [commits/260727_1510_a49e922_run-scribble_feature-docs.md](./commits/260727_1510_a49e922_run-scribble_feature-docs.md) |

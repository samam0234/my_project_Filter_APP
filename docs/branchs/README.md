# branchs — 브랜치 · 커밋 기록

기능 브랜치와 커밋 이력을 **템플릿에 맞춰** 남기는 폴더입니다.  
한 줄 요약만 적는 것은 금지합니다.

## 필수 문서

| 파일 | 설명 |
|------|------|
| [TEMPLATE.md](./TEMPLATE.md) | **커밋 기록 작성 템플릿 (필수 준수)** |
| [BRANCH_MAP.md](./BRANCH_MAP.md) | 브랜치 전략 요약 |
| [commits/](./commits/) | 커밋별 상세 기록 파일 |

## 작성 절차

1. 커밋 완료 후 `TEMPLATE.md`를 복사한다.
2. `commits/{shortsha}-{slug}.md` 로 저장한다.
3. 제목/커밋 번호 · 주 내용 · 상세 · 결과 4섹션을 채운다.
4. (선택) 이 README 표에 링크를 추가한다.

## 기록 목록

| 커밋 | 제목 | 파일 |
|------|------|------|
| `4b1e6ad` | initial project scaffold | [commits/4b1e6ad-initial-scaffold.md](./commits/4b1e6ad-initial-scaffold.md) |
| `1342117` | ignore TypeScript build info | [commits/1342117-ignore-tsbuildinfo.md](./commits/1342117-ignore-tsbuildinfo.md) |
| `8914abe` | schema/router/repo + dual DB | [commits/8914abe-backend-layers-db.md](./commits/8914abe-backend-layers-db.md) |
| `8157388` | cut_and_keep docker stack | [commits/8157388-docker-cut-and-keep.md](./commits/8157388-docker-cut-and-keep.md) |
| `5420cfb` | console + docs hub | [commits/5420cfb-console-and-docs-hub.md](./commits/5420cfb-console-and-docs-hub.md) |

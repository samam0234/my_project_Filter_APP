# 커밋 기록을 branchs/commits 에 필수화 / `f782820`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-28 17:24`  
> 작성자: `while`  
> 파일명: `260728_1724_f782820_branchs-commits-mandatory_feature-docs.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(branchs): 커밋 기록을 branchs/commits 에 필수화` |
| **커밋 번호 (SHA)** | `f782820b48084ee7d434564bc1168afdbab277e2` |
| **짧은 SHA** | `f782820` |
| **브랜치** | `feature/docs` |

## 2. 주 커밋 내용

- 커밋 기록 경로를 **`docs/branchs/commits/` 만** 사용하도록 스킬·규칙에 강제
- `docs/commits/` 경로 사용 금지·기록 생략 금지 명시
- 커밋 전·후 무조건 md 작성 + 기록 파일 커밋 체크리스트
- training README 일본어/띄어쓰기 표현 수정

## 3. 변경 범위

- 수정: `.agents/skills/cutnkeep/SKILL.md`, `.grok/skills/…`, `AGENTS.md`, `.claude/CLAUDE.md`, `.grok/rules/cutnkeep.md`
- 수정: `docs/branchs/README.md`, `TEMPLATE.md`, `docs/guidance/commit-message.md`
- 수정: `training/README.md`
- 삭제: (워킹트리에서) 잘못된 `docs/commits/` 폴더 — 커밋 전 제거됨

## 4. 결과

- 에이전트 로드 규칙에 커밋 기록 필수 당부 반영
- 후속: develop `--no-ff` 병합·푸시

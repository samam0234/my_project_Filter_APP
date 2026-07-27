# 커밋 메시지 가이드 (필수)

Cut & Keep 저장소의 **모든 커밋**은 아래 언어·형식을 따른다.

---

## 1. 언어 규칙

| 구간 | 언어 | 설명 |
|------|------|------|
| **제목 (subject / title)** | **영어만** | Conventional Commits |
| **본문 (body)** | **한국어** | 무엇을·왜 바꿨는지 |
| **바닥글 (footer)** | **한국어** | 이슈 연결, Breaking, 후속 작업 등 |

> 제목에 한글을 넣지 않는다.  
> 본문·바닥글에 영어 코드 식별자(`feature/backend`, `JobRepository`)는 허용.

---

## 2. 전체 형식

```text
<type>(<scope>): <English summary>

<한국어 본문 — 여러 줄 가능>

<한국어 바닥글 — 선택, 여러 줄 가능>
```

### 2.1 제목 (영어)

```text
feat(backend): add job repository and dual database support
fix(docker): map redis host port to 6380
docs(branchs): enforce YYMMDD_HHMM commit log filename
chore(gitignore): ignore TypeScript build info files
```

| 규칙 | 내용 |
|------|------|
| type | `feat` `fix` `docs` `chore` `refactor` `test` `perf` `ci` `style` `build` |
| scope | `backend` `frontend` `console` `docker` `docs` `branchs` `db` 등 |
| 길이 | 제목 한 줄, 권장 72자 이내 |
| 마침표 | 제목 끝 `.` 붙이지 않음 |
| 시제 | 명령형/현재형 (`add`, `fix`, not `added`) |

### 2.2 본문 (한국어)

- 변경 요약 bullet 또는 짧은 문단
- **왜** 필요한지 포함
- 관련 경로·모듈 언급 가능

```text
스키마·라우터·레포지토리 계층을 분리하고
로컬 SQLite / 배포 MariaDB 이중 연결을 추가함.
job·feedback 메타데이터를 DB에 저장하도록 연결함.
```

### 2.3 바닥글 (한국어, 선택)

자주 쓰는 키:

```text
관련: docs/plan/DATABASE.md
후속: feature/console 인증 추가 예정
Breaking: 구 api/endpoints 경로 제거, routers 로 이동
Refs: #12
```

영어 footer 키워드(`Breaking-Change:`)를 쓸 경우 **값 설명은 한국어**로 쓴다.

```text
Breaking-Change: 업로드 응답 필드 before_path 를 before_url 로 변경함
```

---

## 3. 전체 예시

### Good

```text
feat(docs): add ops console app and documentation hub folders

운영 관리자 console(React/TS)을 루트에 추가하고
Architecture, branchs, guidance 등 문서 허브 폴더를 구성함.

관련: docs/README.md, console/README.md
후속: develop 병합 및 콘솔 인증 검토
```

### Bad

```text
feat(docs): 콘솔이랑 문서 추가함          ← 제목 한글 금지
작업함                                    ← type/scope/영어 제목 없음
feat(backend): add DB                     ← 본문 없음(가능은 하나 비권장)
```

---

## 4. 커밋 후 필수 후속

1. `docs/branchs/TEMPLATE.md` 형식으로 기록 파일 작성  
2. 파일명: `YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md`  
   - 예: `260727_1446_5420cfb_console-and-docs-hub_feature-docs.md`  
   - `HHMM` = 시분 (커밋 시각)  
3. `docs/branchs/README.md` 목록 표 갱신  

---

## 5. 브랜치

- **작업·커밋:** `feature/*` 등 작업 브랜치에서만  
- **일자 통합 병합:** **`develop` 또는 `main` 에만** 붙인다  
- feature 완료 시 → **`develop` merge** (feature끼리 장기 합치기 금지)  
- 상세: `docs/guidance/branch-merge.md`, `docs/branchs/BRANCH_MAP.md`

---

## 6. 에이전트

AI 에이전트는 커밋 시 이 문서를 따른다.  
프로젝트 스킬 진입점: `.agents/skills/cutnkeep/SKILL.md`, 루트 `AGENTS.md`, 각 도구 폴더(`.grok`, `.claude`, `.cursor` 등).

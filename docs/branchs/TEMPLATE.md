# 커밋 기록 템플릿

아래 형식을 **그대로** 복사해 `commits/` 아래 새 파일을 만든다.

---

## Git 커밋 메시지 규칙 (필수)

커밋 **자체**의 메시지 언어:

| 구간 | 언어 |
|------|------|
| **제목 (title/subject)** | **영어만** |
| **본문 (body)** | **한국어** |
| **바닥글 (footer)** | **한국어** |

```text
feat(scope): english summary only

한국어 본문 — 변경 이유와 내용

관련: …          ← 바닥글도 한국어
후속: …
```

상세 가이드: [`docs/guidance/commit-message.md`](../guidance/commit-message.md)  
에이전트 스킬: `.agents/skills/cutnkeep/SKILL.md`

---

## 파일명 규칙 (필수)

```text
YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

| 조각 | 규칙 | 예시 |
|------|------|------|
| `YYMMDD` | 연 뒤2 + 월2 + 일2 (구분자 없음) | `260727` (2026-07-27) |
| `HHMM` | **시·분** 24시간제 4자리 | `1446` (14시 46분) |
| `커밋ID` | short SHA (보통 7자) | `8914abe` |
| `커밋이름` | 소문자 kebab (공백·`/` 금지) | `backend-layers-db` |
| `커밋브랜치` | `/` → `-` | `feature-backend` |

### 올바른 예

```text
260727_1220_8914abe_backend-layers-db_feature-backend.md
260727_1303_8157388_docker-cut-and-keep_feature-backend.md
260727_1446_5420cfb_console-and-docs-hub_feature-docs.md
```

### 잘못된 예

```text
26_07_27_8914abe_....md              ← 날짜를 언더스코어로 쪼갬 (구 규칙)
260727_8914abe_backend-layers-db.md  ← 시분(HHMM) 없음
260727_14_46_8914abe_....md          ← 시·분 사이에 언더스코어 (HHMM 한 덩어리)
260727_1446_8914abe_backend layers.md ← 공백
260727_1446_8914abe_x_feature/backend.md ← 슬래시
```

- **날짜·시각**: 커밋 시각(로컬, `git log` 기준) 권장. 기록 작성 시각도 가능하나 일관되게 쓸 것.
- Windows 예: `git log -1 --format=%ci` → `2026-07-27 14:46:50 +0900` → `260727_1446`

---

## 본문 템플릿

```markdown
# {제목} / `{full_or_short_sha}`

> 브랜치: `{branch_name}`  
> 작성일: `YYYY-MM-DD HH:MM`  
> 작성자: `{name}`  
> 파일명: `YYMMDD_HHMM_[커밋ID]_[커밋이름]_[커밋브랜치].md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `{conventional commit subject, English}` |
| **커밋 번호 (SHA)** | `{full sha}` |
| **짧은 SHA** | `{7-char}` |
| **브랜치** | `{feature/xxx 또는 develop}` |
| **부모 커밋** | `{parent sha or -}` |

## 2. 주 커밋 내용

- (핵심 변경을 3~7개 bullet으로)
- …

## 3. 상세 내용

### 3.1 배경 / 목적
왜 이 커밋이 필요했는지.

### 3.2 변경 범위
- 추가된 경로:
- 수정된 경로:
- 삭제된 경로:

### 3.3 기술 포인트
설계·API·DB·Docker 등 중요한 결정.

### 3.4 의도적으로 하지 않은 것
스코프 밖 / 후속으로 미룬 작업.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [ ] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술:

### 4.2 부작용 / 리스크
알려진 이슈, 포트 충돌, 미구현 등.

### 4.3 후속 작업
다음에 이어서 할 일, 관련 브랜치.

### 4.4 관련 문서
- `docs/...`
```

---

## 작성 금지 사항

- 제목만 한 줄 적고 끝내기
- “버그 수정함”, “작업함” 수준의 모호한 상세
- SHA 없이 브랜치만 적기
- **날짜·시분 없는 파일명** / 구 규칙(`26_07_27_...`) 사용

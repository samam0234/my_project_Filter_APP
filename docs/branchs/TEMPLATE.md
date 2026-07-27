# 커밋 기록 템플릿

아래 형식을 **그대로** 복사해 `commits/` 아래 새 파일을 만든다.

---

## 파일명 규칙 (필수)

```text
YY_MM_DD_[커밋ID]_[커밋이름]_[커밋브랜치].md
```

| 조각 | 규칙 | 예시 |
|------|------|------|
| `YY` | 연도 뒤 2자리 | `26` (2026) |
| `MM` | 월 2자리 | `07` |
| `DD` | 일 2자리 | `27` |
| `커밋ID` | short SHA (보통 7자) | `8914abe` |
| `커밋이름` | 소문자 kebab 또는 snake (공백·`/` 금지) | `backend-layers-db` |
| `커밋브랜치` | 브랜치명, `/` 는 `-` 로 치환 | `feature-backend` |

### 올바른 예

```text
26_07_27_8914abe_backend-layers-db_feature-backend.md
26_07_27_8157388_docker-cut-and-keep_feature-backend.md
26_07_27_5420cfb_console-and-docs-hub_feature-docs.md
```

### 잘못된 예

```text
8914abe-backend-layers-db.md          ← 날짜 없음
26-07-27_8914abe_....md               ← 구분자 `-` 대신 `_` 사용
26_07_27_8914abe_backend layers.md    ← 공백
26_07_27_8914abe_x_feature/backend.md ← 슬래시
```

날짜는 **커밋 작성일(또는 기록 작성일)** 기준으로 붙인다.

---

## 본문 템플릿

```markdown
# {제목} / `{full_or_short_sha}`

> 브랜치: `{branch_name}`  
> 작성일: `YYYY-MM-DD`  
> 작성자: `{name}`  
> 파일명: `YY_MM_DD_[커밋ID]_[커밋이름]_[커밋브랜치].md`

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
- **날짜 없는 파일명** / 규칙과 다른 파일명

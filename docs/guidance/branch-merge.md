# 브랜치 작업 · 병합 가이드 (필수)

Git Graph가 일자로 보이도록, **통합 라인은 `develop` / `main` 만** 쓰고  
기능 작업은 **각자 `feature/*` 등에서** 한다.

---

## 1. 핵심 원칙

| 구분 | 규칙 |
|------|------|
| **일상 커밋 · 작업** | `feature/*`, `bugfix/*`, `experimental/*` 등 **작업 브랜치에서만** |
| **일자로 합치는 통합 라인** | **`develop` 또는 `main` 만** |
| **feature → 통합** | 작업이 끝난 뒤 **`develop`에 merge** 할 때만 붙인다 |
| **배포 라인** | `release/*` 검증 후 **`main`에 merge** |

> 여러 feature를 서로 합치거나, feature끼리 길게 꼬지 않는다.  
> **합치는 창구는 develop (개발 통합) / main (배포) 뿐이다.**

---

## 2. 권장 흐름

```text
develop
  │
  ├─ checkout -b feature/xxx
  │     … 커밋 (작업 브랜치에서만)
  │
  └─ develop 에 merge  ← 여기서만 통합 라인에 붙음
        │
        └─ (안정 시) release/* → main
```

### 2.1 작업 시작

```bash
git checkout develop
git pull origin develop   # 원격 있으면
git checkout -b feature/opencv
# … 작업 및 커밋 …
```

### 2.2 작업 중

- **커밋은 현재 feature 브랜치에만** 쌓는다.
- `develop` / `main` 에 직접 기능 커밋하지 않는다.  
  (문서 긴급 핫픽스 등 예외는 최소화)

### 2.3 develop 에 붙이기 (통합)

```bash
git checkout develop
git pull origin develop
git merge feature/opencv
# 또는 PR: feature/opencv → develop
git push origin develop
```

- **일자 히스토리(FF)를 원할 때:** feature가 develop 최신에서 분기했고 충돌이 없으면  
  `git merge` 가 fast-forward 되어 그래프가 일직선으로 이어진다.
- **갈림길을 남기고 싶을 때:**  
  `git merge --no-ff feature/opencv` (명시적 merge 커밋)  
  → 기본 정책은 **일자 통합 선호 FF 허용**. 감사용 분기가 필요하면 `--no-ff` 를 문서에 남기고 사용.

### 2.4 main 에 붙이기 (배포)

```bash
git checkout -b release/0.1.0 develop
# 검증 …
git checkout main
git merge release/0.1.0   # 또는 develop 안정 태그 기준
git tag v0.1.0
```

- 일상 feature를 **직접 main에 merge 하지 않는다.**
- main 은 배포·핫픽스 창구만.

---

## 3. 하지 말 것

| 금지 | 이유 |
|------|------|
| feature A 를 feature B 에 장기간 merge 하며 통합 | 통합 라인이 여러 갈래로 지저분해짐 |
| feature 브랜치끼리만 합치고 develop 미반영 | develop 이 진짜 통합본이 아님 |
| develop 없이 main 에 feature 직행 | 배포 라인 오염 |
| 모든 작업을 develop 에 직접 커밋 | feature 단위 이력·리뷰 불가, 그래프 의미 없음 |

---

## 4. 그래프가 일자로 보이는 경우 (정상)

다음이면 Git Graph 가 **직선**에 가깝다 — 버그가 아니다.

1. 작업은 feature 에서 했지만  
2. develop 병합이 **fast-forward** 이고  
3. feature 가 develop 최신에서 짧게 분기한 경우  

**의도:** 통합 라인(`develop`/`main`)은 깨끗하게 일자로 유지하고,  
작업 단위 분리는 **브랜치 이름 + 커밋 메시지 + `docs/branchs/commits/` 기록**으로 한다.

---

## 5. 체크리스트

- [ ] 기능 작업 브랜치: `feature/...` (또는 bugfix/experimental)
- [ ] 해당 브랜치에서만 커밋
- [ ] 완료 후 **develop 에만** merge
- [ ] 배포 시 **main** (release 경유 권장)
- [ ] 커밋 메시지: 제목 영어 / 본문·바닥글 한국어
- [ ] `docs/branchs/commits/YYMMDD_HHMM_...md` 기록

---

## 6. 관련 문서

- `docs/branchs/BRANCH_MAP.md`
- `docs/plan/LOGIC_AND_GIT_BRANCH_STRATEGY.md`
- `docs/guidance/commit-message.md`
- `.agents/SKILL.md`

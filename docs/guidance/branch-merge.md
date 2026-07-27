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

### 2.3 develop 에 붙이기 (통합) — **반드시 `--no-ff`**

```bash
git checkout develop
git pull origin develop
# 금지: git merge feature/opencv   ← FF 되면 그래프가 다시 일자로 합쳐짐
git merge --no-ff feature/opencv -m "merge: feature/opencv into develop"
git push origin develop
```

| 규칙 | 내용 |
|------|------|
| **필수** | `develop` / `main` 합류 시 **`git merge --no-ff`** |
| **금지** | feature → develop **fast-forward** (일직선 그래프 원인) |
| **금지** | 일상 작업을 develop 에 직접 커밋하고 feature 포인터만 따라가기 |

### 2.4 main 에 붙이기 (배포)

```bash
git checkout -b release/0.1.0 develop
# 검증 …
git checkout main
git merge --no-ff release/0.1.0 -m "merge: release/0.1.0 into main"
git tag v0.1.0
```

- 일상 feature를 **직접 main에 merge 하지 않는다.**
- main 은 배포·핫픽스 창구만. `merge --no-ff` 권장.

---

## 3. 하지 말 것

| 금지 | 이유 |
|------|------|
| feature A 를 feature B 에 장기간 merge 하며 통합 | 통합 라인이 여러 갈래로 지저분해짐 |
| feature 브랜치끼리만 합치고 develop 미반영 | develop 이 진짜 통합본이 아님 |
| develop 없이 main 에 feature 직행 | 배포 라인 오염 |
| 모든 작업을 develop 에 직접 커밋 | feature 단위 이력·리뷰 불가, 그래프 의미 없음 |

---

## 4. 그래프가 일자로만 보이던 원인 (피해야 할 패턴)

1. feature 를 만들었지만 **커밋 없이** develop 과 같은 tip 만 가리킴  
2. develop 병합을 **fast-forward** 로 함 (`merge` 기본 동작)  
3. 실제 작업을 **한 브랜치 체인**에만 쌓고 다른 feature 는 중간 커밋 포인터만 둠  

**현재 정책:** feature 는 develop 에서 분기한 뒤 **반드시 자기 커밋**을 쌓고,  
합칠 때는 **`--no-ff`**. 빈 작업 브랜치도 tip 이 develop 과 같지 않도록 앵커 커밋을 둘 수 있다.

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

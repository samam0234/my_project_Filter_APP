# 프론트·콘솔 vitest 테스트와 GitHub Actions CI / `56d13d92c8dd39fb787187690b6ba71575e3929b`

> 브랜치: `feature/ops-hardening`  
> 작성일: `2026-10-06 05:24`  
> 작성자: `agent`  
> 파일명: `261006_0524_56d13d9_frontend-tests-ci_feature-ops-hardening.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `test(frontend): 프론트·콘솔 vitest 테스트와 GitHub Actions CI` |
| **커밋 번호 (SHA)** | `56d13d92c8dd39fb787187690b6ba71575e3929b` |
| **짧은 SHA** | `56d13d9` |
| **브랜치** | `feature/ops-hardening` |
| **부모 커밋** | `ab79eda` |

## 2. 주 커밋 내용

- frontend 16건 · console 4건 vitest 테스트 (이전 0건)
- `.github/workflows/ci.yml` — backend · frontend · console 3개 job
- axios 취약점 해소 (1.18.1 → 1.20.0)

## 3. 상세 내용

### 3.1 배경 / 목적

완성도 점검 2번 (프론트 테스트 0건 · CI 없음). 사용자 요청 "6번은 차근히 하면서 2번 진행".

### 3.2 변경 범위

- 추가: `.github/workflows/ci.yml`, `{frontend,console}/vitest.{config,setup}.ts`,
  `frontend/src/{router,utils/formatters,store/useAuthStore,components/auth/RequireLogin,components/prompt/PromptInput}.test.ts[x]`,
  `console/src/pages/LearningPage.test.tsx`
- 수정: `{frontend,console}/{package.json, package-lock.json, tsconfig.app.json}`, `tests/{README.md, requirements-test.txt}`,
  `docs/plan/TESTING.md`

### 3.3 기술 포인트

- 테스트 파일은 `tsconfig.app.json` exclude → `tsc -b` 프로덕션 빌드와 분리 (vitest 는 esbuild 로 변환)
- jsdom 에 없는 `window.scrollTo` 는 `vitest.setup.ts` 에서 대체
- CI 백엔드는 모델 없이 (`requirements.docker.txt` + `tests/requirements-test.txt`), 학습 DB=SQLite.
  깨끗한 venv·`.env` 없는 위치에서 재현 → 처음에 1건 실패(CI 환경변수가 테스트 전제를 바꿈) 발견·수정 후 204 passed
- `npm audit fix --omit=dev` 가 devDependencies 를 node_modules 에서 지워 빌드가 깨지는 것을 확인 → 재설치

### 3.4 의도적으로 하지 않은 것

- dev 도구 취약점 10건(vite 5·esbuild·eslint·nanoid) — vite 메이저 업그레이드 필요, 배포 번들 영향 없음 → 별도 작업
- E2E(브라우저) 테스트 (Playwright 등)
- 원격 push (CI 실제 실행은 push 후)

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] frontend `npm test` 16 passed, `npm run build` 성공
- [x] console `npm test` 4 passed, `npm run build` 성공
- [x] 배포 번들 `npm audit --omit=dev` 0건 (두 앱)
- [x] CI 조건 백엔드 재현 204 passed, CI preflight 단계 exit 0
- [x] 로컬 pytest 전체 통과

### 4.2 부작용 / 리스크

- package-lock 변경 (vitest·Testing Library·jsdom 추가, axios 갱신)

### 4.3 후속 작업

- push 후 Actions 실제 실행 확인
- vite 메이저 업그레이드 (dev 취약점)
- 1번 배포 (Oracle Cloud · Vercel/Cloudflare) — 사용자 보류

### 4.4 관련 문서

- `docs/plan/TESTING.md`

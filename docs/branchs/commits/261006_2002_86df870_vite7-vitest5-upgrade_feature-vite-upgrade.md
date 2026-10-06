# vite 7 · vitest 5 로 개발 도구 업그레이드 / `86df870425988670de992d06c9cdcc3b9dd1d846`

> 브랜치: `feature/vite-upgrade`  
> 작성일: `2026-10-06 20:02`  
> 작성자: `agent`  
> 파일명: `261006_2002_86df870_vite7-vitest5-upgrade_feature-vite-upgrade.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `chore(deps): vite 7 · vitest 5 로 개발 도구 업그레이드` |
| **커밋 번호 (SHA)** | `86df870425988670de992d06c9cdcc3b9dd1d846` |
| **짧은 SHA** | `86df870` |
| **브랜치** | `feature/vite-upgrade` |
| **부모 커밋** | `6edd18b` (develop) |

## 2. 주 커밋 내용

- frontend · console: vite 5.4 → 7.3, @vitejs/plugin-react 4 → 5, vitest 2 → 5
- Node 22.12 이상 요구에 맞춰 `engines` · CI · frontend Docker 빌드 이미지 · 문서

## 3. 상세 내용

### 3.1 배경 / 목적

남은 항목 "개발 도구(vite) 메이저 업그레이드". 이전 점검에서 `npm audit`(dev 포함) 10건(치명 2)이 vite 5 · esbuild · vitest 계열이었다.

### 3.2 변경 범위

- 수정: `{frontend,console}/{package.json, package-lock.json}`, `.github/workflows/ci.yml`, `frontend/Dockerfile`,
  `RUN.md`, `docs/guidance/getting-started.md`, `docs/web_management/pre-deploy.md`

### 3.3 기술 포인트

- 두 단계로 올림: vite 7 + plugin-react 5 + vitest 3 (esbuild 취약점 해소) → vitest 5 (tinypool 치명 취약점 해소, Node 22.12 요구)
- vite 7 은 Node ^20.19, vitest 5 는 ^22.12 → `engines: >=22.12`, CI `node-version: 22`, `frontend/Dockerfile` `node:22-alpine`
- `npm audit fix --omit=dev` 는 devDependencies 를 지워 빌드가 깨짐 (이전 작업에서 확인) — 이번엔 쓰지 않음

### 3.4 의도적으로 하지 않은 것

- **tailwindcss 3 → 4**: 남은 취약점 7건이 전부 이 계열(braces · chokidar · postcss-selector-parser, 빌드 시점). 설정·CSS 지시어 마이그레이션이 필요해 범위 밖
- eslint · typescript 메이저

## 4. 커밋 관련 결과

### 4.1 동작 결과

| 항목 | 이전 | 이후 |
|------|------|------|
| `npm audit` (dev 포함) | 10건 (치명 2 · 높음 5+ · 중간) | **7건 (높음 5 · 중간 2, 치명 0)** — 전부 tailwindcss 3 계열 |
| 배포 번들 audit | 0건 | 0건 |

- [x] frontend vitest 16 · console vitest 4 통과, 두 앱 `npm run build` 성공
- [x] vite 7 개발 서버에서 브라우저 직접 확인 9/9 · 오류 0건 (`scripts/experiments/ui_check.py`)
- [x] `docker compose build frontend` 성공 (node:22-alpine)

### 4.2 부작용 / 리스크

- Node 22.12 미만 환경에서는 `npm test` · `npm run dev` 가 안 됨 (`engines` 로 경고)
- 다른 PC 는 `npm ci` 를 다시 해야 함

### 4.3 후속 작업

- tailwindcss 4 마이그레이션 (화면 회귀는 `ui_check.py` 로 확인 가능)

### 4.4 관련 문서

- `docs/web_management/pre-deploy.md`

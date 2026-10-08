# 컷앤킵 — 테스트 전략

**목적:** 서버·학습 실행 전에 구조와 핵심 로직이 깨지지 않았는지 빠르게 확인한다.

**코드 위치:** 저장소 루트 `tests/`  
**실행 설정:** 루트 `pytest.ini`  
**러너 의존성:** `tests/requirements-test.txt` (+ 루트 `requirements.txt`)

---

## 1. 테스트 계층

| 계층 | 경로 | 의존성 | 역할 |
|------|------|--------|------|
| **structure** | `tests/structure/` | 거의 없음 | 폴더·README·plan 문서·스킬 경로 존재 |
| **unit** | `tests/unit/` | pydantic, numpy, opencv 등 | 스키마, config, 휴리스틱, LLM 파싱, 대상 필터, 인스턴스 선택, 검증, 효과, LoRA 데이터 |
| **smoke** | `tests/smoke/` | backend 패키지 | import · FastAPI 앱 생성 |

향후 확장:

| 계층 | 설명 |
|------|------|
| **api** | TestClient 로 `/health`, `/upload` (가중치 없이도 stub 가능) |
| **e2e** | 실제 yolo26m-seg + Ollama 연동 (수동/CI 옵션) |

---

## 2. 실행 전 체크리스트 (권장 순서)

```text
1) pytest tests/structure   ← 골격 (문서·폴더)
2) pip install backend + tests deps
3) pytest tests/unit
4) pytest tests/smoke
5) (선택) 수동: RUN.md 따라 서버 기동 + docs/vaildates/
```

한 줄:

```powershell
cd d:\my_project\CutNKeep
pytest
```

---

## 3. 프로젝트 구조와의 대응

| 영역 | 테스트로 보장하는 것 |
|------|----------------------|
| `backend/app/*` | import, 스키마, 보안, 휴리스틱, 검증, 효과 |
| `training/` | 스크립트·config 파일 존재 |
| `docs/plan/*` | 핵심 plan md 존재 (`TESTING.md` 포함) |
| `docs/*` 허브 | Architecture, branchs, guidance 등 README |
| `.agents/skills/` | 스킬 경로 존재 |
| `console/`, `frontend/` | README 존재 (빌드는 별도) |

---

## 4. CI — `.github/workflows/ci.yml`

push(`main`·`develop`·`feature/**`·`fix/**`) · PR(`main`·`develop`) 마다 3개 job 이 병렬로 돈다.

| job | 내용 |
|-----|------|
| backend | Python 3.11 · `requirements.docker.txt` + `tests/requirements-test.txt` (모델 없음, 학습 DB=SQLite) → `pytest` → 안전한 production 값으로 `python -m app.core.preflight` |
| frontend | Node 20 · `npm ci` → `npm test`(vitest) → `npm run build` → `npm audit --omit=dev --audit-level=high` |
| console | frontend 와 같음 |

- 모델(ultralytics·torch)이 필요한 테스트는 `importorskip` 으로 건너뛰고 세그는 stub 마스크로 동작
- 로컬 전체: 2026-10-09 기준 **백엔드 405 · 프론트 50 · 콘솔 21** 통과
- 로컬에서 CI 와 같은 조건 확인 (2026-10-06, 깨끗한 venv · `.env` 없이 204 passed — 이후 테스트가 늘었다):
  `pip install -r requirements.docker.txt -r tests/requirements-test.txt` 후 `.env` 가 없는 폴더에서 pytest
- 아직 원격에 push 하지 않아 실제 Actions 실행은 확인 전

### 프론트 · 콘솔 테스트 (vitest + Testing Library, jsdom)

```powershell
cd frontend; npm test      # 50건 — 회원 전용 화면, 로그인, 라우터, 프롬프트 입력, 배치, 영상, GIF 탭, 작업 기록(종류 필터), 포맷
cd console;  npm test      # 21건 — 학습 데이터 검수, 회원 관리, 시스템·정리, 로그인
```

테스트 파일(`*.test.ts[x]`)은 `tsconfig.app.json` 에서 빼 프로덕션 빌드와 분리한다.

### 테스트가 실제 데이터를 건드리지 않게

- API 테스트는 `tests/unit/conftest.py` 의 `api_env` — 메모리 SQLite, 업로드·피드백 폴더를 임시 폴더로
- 업로드를 만드는 서비스 테스트도 `monkeypatch.setattr(get_settings(), "upload_dir", tmp)` 로 (실제 `backend/data/uploads` 금지)
- 설정 기본값을 검사하는 테스트는 로컬 `.env` 에 흔들리지 않게 값을 직접 넣는다 (`test_preflight.py` 의 `DEV_DEFAULTS`)
- 호스트에서 `uvicorn --reload` 가 떠 있으면 코드를 고칠 때마다 재시작하며 기동 작업(자동 정리 · 백업)이 실제 `backend/data` 에서 돈다 — 테스트와 무관하지만 헷갈리지 말 것

---

## 5. 관련 문서

| 문서 | 내용 |
|------|------|
| `tests/README.md` | 실행 방법 |
| `docs/vaildates/mvp-checklist.md` | 수동 MVP 체크 |
| `docs/vaildates/api-smoke.md` | curl 스모크 |
| `docs/plan/PROJECT_STRUCTURE.md` | 폴더 트리 |
| `RUN.md` | 서버 기동 |

---

## 6. 규칙

- 새 핵심 모듈 추가 시 unit 테스트 1개 이상 권장  
- 무거운 GPU 학습 테스트는 `training/` CI 와 분리  
- 실패 시 `docs/find_debug/` 에 원인 기록 권장  

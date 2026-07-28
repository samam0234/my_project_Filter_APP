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
| **unit** | `tests/unit/` | pydantic, numpy, opencv 등 | 스키마, config, 휴리스틱, 검증, 효과 |
| **smoke** | `tests/smoke/` | backend 패키지 | import · FastAPI 앱 생성 |

향후 확장:

| 계층 | 설명 |
|------|------|
| **api** | TestClient 로 `/health`, `/upload` (가중치 없이도 stub 가능) |
| **e2e** | 실제 YOLO26n-seg + Ollama 연동 (수동/CI 옵션) |

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

## 4. CI 제안 (향후)

```yaml
# 예: GitHub Actions 스케치
# - Python 3.11
# - pip install -r requirements.txt -r tests/requirements-test.txt
# - pytest tests/structure tests/unit tests/smoke
```

Docker 이미지 빌드와 분리해 **가벼운 unit** 을 먼저 돌리는 것을 권장.

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

# tests — 실행 전 검증

서비스/학습을 돌리기 **전에** 구조·스키마·핵심 로직이 깨지지 않았는지 확인하는 테스트 구역이다.

## 구조

```text
tests/
├── README.md
├── conftest.py              # 공통 fixture, path
├── unit/                    # 단위 테스트 (DB/서버 불필요 위주)
│   ├── test_schemas.py
│   ├── test_config.py
│   ├── test_prompt_heuristic.py
│   ├── test_validator.py
│   ├── test_security.py
│   └── test_effects.py
├── structure/               # 폴더·문서·스크립트 존재 검사
│   └── test_project_layout.py
└── smoke/                   # 가벼운 import 스모크
    └── test_imports.py
```

## 실행 방법

### 전체

```powershell
cd d:\my_project\CutNKeep

# backend venv (Python 3.11 권장) 활성화 후
pip install -r backend/requirements.txt
pip install -r tests/requirements-test.txt

pytest
```

### 일부만

```powershell
pytest tests/structure -q          # 폴더/문서 골격만 (의존성 최소)
pytest tests/unit -q               # 단위
pytest tests/smoke -q              # import 스모크
pytest tests/unit/test_schemas.py  # 단일 파일
```

OpenCV/numpy 가 없으면 `test_effects` 등은 **자동 skip** 될 수 있다.

## 언제 돌리나

| 시점 | 권장 |
|------|------|
| 커밋 전 | `pytest tests/structure tests/unit` |
| 백엔드 의존성 설치 후 | `pytest` 전체 |
| Docker 배포 전 | 구조 + unit + (가능하면) API 스모크 수동 |
| 학습(`training/`) 전 | structure + YOLO 관련 path 확인 |

## 관련 문서

- `docs/plan/TESTING.md` — 테스트 전략
- `docs/plan/PROJECT_STRUCTURE.md`
- `docs/vaildates/` — 수동 체크리스트
- `RUN.md` — 서버 기동

## 추가 가이드

새 모듈을 만들면 가능하면 `tests/unit/` 에 대응 테스트를 추가한다.  
E2E(실제 업로드·YOLO 추론)는 모델 가중치가 있을 때 별도 확장.

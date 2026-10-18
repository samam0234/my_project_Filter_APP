# tests — 백엔드 · 도구 · 문서 검증

> 서버를 띄우거나 모델을 학습하기 **전에**, 구조 · 규칙 · 핵심 로직이 깨지지 않았는지 확인한다. 모델 가중치와 네트워크 없이도 대부분 돈다.

이 폴더는 백엔드(`backend/app`)와 스크립트(`scripts/` · `training/`), 그리고 **문서와 코드의 일치**를 검사하는 pytest 구역이다.
사용자 앱과 콘솔의 테스트는 각 앱 안에 있다 (`frontend/src/**/*.test.tsx` · `console/src/**/*.test.tsx`).

| 구역 | 개수 (2026-10-12 인수인계) | 위치 |
|------|----------------------------|------|
| 백엔드 · 도구 · 문서 | **505** | 이 폴더 (pytest) |
| 사용자 앱 | 95 | `frontend/` (Vitest) |
| 운영 콘솔 | 21 | `console/` (Vitest) |

2026-10-10의 463 · 65 · 21은 그 전 기록이라 지금 숫자로 쓰지 않는다.

---

## 1. 원칙

- **실제 데이터를 건드리지 않는다.** 업로드 · 피드백 폴더는 임시 폴더로, 서비스 DB · 학습 DB는 엔진 싱글톤까지 메모리 DB로 바꾼다 (라우터 밖 직접 세션 포함).
- **밖으로 나가지 않는다.** 메일은 가로채고, Ollama · LLM은 가짜 응답으로, 네트워크 · Docker가 필요한 도구는 흉내 낸다.
- **모델 없이 돈다.** YOLO는 가짜 세그(사람 2명 등)나 합성 이미지로 대신한다. 정말 모델이 필요한 테스트는 `importorskip`으로 건너뛴다.
- **개인 `.env`에 영향받지 않는다.** 설정은 `Settings(...)`에 값을 직접 넣는다 — 개인 SMTP 값 때문에 한 번 깨진 적이 있다.
- **문서도 검사한다.** 코드에 생긴 기능이 문서에서 빠지면 실패한다 (아래 `structure/`).

---

## 2. 구성

```text
tests/
├── conftest.py              공통 fixture · 경로
├── requirements-test.txt    pytest · httpx (백엔드 의존성 위에 추가)
├── unit/                    단위 · API 테스트 (DB · 서버 불필요 위주)
│   └── conftest.py          api_env — 메모리 SQLite 앱 + 메일 가로채기
├── structure/               폴더 · 핵심 파일 · 문서 등록 검사
└── smoke/                   핵심 모듈 import 스모크
```

설정은 루트 `pytest.ini`에 있다 (`testpaths = tests`, `pythonpath = backend`, `-q --tb=short`).

### unit — 기능별

**계정 · 접근 · 보안**

| 파일 | 검사 |
|------|------|
| `test_auth.py` | 가입 · 로그인 잠금 · 세션 · 아이디 찾기 · 비밀번호 재설정 · 내 계정(이름 · 비밀번호 변경 · 전체 로그아웃 · 탈퇴) |
| `test_signup_verify.py` | 이메일 인증 가입 — 신청(메일) → 일련번호 → 가입 완료 · 만료 · 횟수 · 재발송 · 우회 차단 · 정리 |
| `test_mail_templates.py` | HTML 메일 템플릿 · multipart 발송 · 메일 속 버튼 주소(`site_url`) |
| `test_access.py` | 비로그인은 처리 · 다운로드만 · 회원은 본인 작업만 · 배치 · 콘솔 loopback |
| `test_security.py` · `test_security_hardening.py` | 업로드 확장자 · MIME · 압축 폭탄(사진 · GIF · 영상 해상도) · 프록시 뒤 IP · 자동 백업 · 자동 정리(`.gitkeep` 보호) |
| `test_ratelimit.py` | 비로그인 IP · 회원 계정 기준 속도 제한, 429 + `Retry-After` |
| `test_preflight.py` | 운영 설정 점검 · 보안 헤더 |

**문장 해석**

| 파일 | 검사 |
|------|------|
| `test_prompt_heuristic.py` · `test_heuristic_targets.py` | 키워드 파서 — "X 말고 Y만", 풍경, 영어, 역할 규칙(남길 것 · 뺄 것 · 지울 것) |
| `test_prompt_llm.py` | LLM provider 요청 · 파싱 · selector 정규화 (네트워크 없음) |
| `test_prompt_chain.py` | 해석 체인 — 키워드 파서와 같으면 1번, 다르면 다수결 |
| `test_prompt_rag.py` | 승인 샘플 RAG — 적재 · 우선순위 · 검색 · 지시문 주입 |
| `test_prompt_chroma.py` · `test_chroma_feedback.py` | Chroma — 글자 검색이 놓친 확인 문장 한 건 보태기 · 확인된 피드백만 색인 · 먼 문장은 꺼내지 않기 |
| `test_llm_models.py` | 해석 모델 선택 (모델 목록 · 사진 · GIF · 영상 요청) |
| `test_chat.py` | 에이전트에게 묻기(AI 채팅) — 모델 선택 · 제한 · 오류 (가짜 Ollama) |

**비전 · 효과 · 파이프라인**

| 파일 | 검사 |
|------|------|
| `test_segmentation_filter.py` | YOLO 대상 라벨 필터 · 별칭 · ONNX 가드 (가짜 YOLO) |
| `test_stuff_segmentation.py` | 배경 덩어리 SegFormer — 어휘 정규화 · 묶음 확률 · Segmentor 연결 |
| `test_instance_selector.py` | 위치 · 개수 · 색 속성 선택 (합성 이미지) |
| `test_mask_exclusion.py` | 지정하지 않은 대상이 섞이지 않게 — 겹침 덜어내기 · 금지 구역 |
| `test_validator.py` | 마스크 검증 ok / fallback / failed |
| `test_effects.py` · `test_edge_tuning.py` | 효과 · GrabCut 제한 · `remove_object` · 경계 다듬기 · 영상 시간축 스무딩 |
| `test_pipeline_graph.py` | LangGraph 재시도 전략 · 최선 시도 채택 · 노드 시간 측정 · 기본값 |
| `test_onnx_inference.py` | 직접 구현한 ONNX 세그 추론 (합성 출력) |
| `test_model_fetch.py` | 큰 모델 받기 · LaMa가 나중에 생겨도 로드 |

**영상 · GIF · 배치**

| 파일 | 검사 |
|------|------|
| `test_batch_api.py` | 배치 · 영상이 단일 업로드와 같은 파이프라인을 타는지 (가짜 세그 — 사람 2명) |
| `test_media_history.py` | 영상 · GIF 작업 기록 · GIF 처리(투명 · WebP) · LaMa / Telea 선택 · 콘솔 파일 |
| `test_instance_tracker.py` | 고른 대상 따라가기 |
| `test_video_inpaint.py` | 영상 · GIF 지우기 배경판 |
| `test_phase2.py` | 배치 진행률 · 영상 마스크 유지 · 오픈 보캐브 폴백 · LoRA 템플릿 공유 |

**DB · 학습 · 운영**

| 파일 | 검사 |
|------|------|
| `test_learning_db.py` | 서비스 DB / 학습 DB 분리 · 사이드카 동기화 · MariaDB 대체 |
| `test_learning_review.py` | 학습 데이터 검수 — 회원 요청 후보 · 승인 · 거절 · 정답 수정 · 일괄 |
| `test_feedback_images.py` | 실패 · 확신 낮은 요청 사진 보관 기간 정리 · 계정 삭제 |
| `test_sqlite_integrity.py` | 서비스 DB 손상 감지 · 호스트 / Docker 파일 분리 기본값 |
| `test_service_db_import.py` | 서비스 DB를 SQLite → MariaDB로 옮기기 |
| `test_console_system.py` · `test_console_users.py` | 콘솔 시스템 화면 · 회원 관리(파일 포함 삭제) |
| `test_config.py` · `test_schemas.py` | 설정 기본 동작 · Pydantic 스키마 |

**학습 · 배포 도구**

| 파일 | 검사 |
|------|------|
| `test_lora_dataset.py` · `test_lora_compositional.py` | `training/lora` 데이터 계약 · 시드 · 평가셋 누수 차단 · 조합형 시드 생성기 (torch 불필요) |
| `test_retrain_yolo.py` | YOLO 재학습 루프 — 어려운 사례 판별 · 채택 판정 (학습 없이) |
| `test_seg_labeling.py` | 실패 사진 라벨링 묶음 — 사례 고르기 · 라벨 검사 · 클래스 순서 |
| `test_deploy_tools.py` | `deploy_check.py` · `models_bundle.py` (네트워크 · Docker 없이) |

### structure — 구조와 문서

| 파일 | 검사 |
|------|------|
| `test_project_layout.py` | 주요 폴더 · 핵심 파일 · README 존재 |
| `test_docs_coverage.py` | **문서 등록 검사** — 모든 API 엔드포인트가 `docs/API_DOCUMENTATION.md`에 · 모든 설정(Settings alias)이 `.env.example`과 문서 어딘가에 · 사용자 앱의 모든 화면 경로가 `docs/guidance/user-frontend.md`와 `frontend/README.md`에 · `docs/FEATURES.md`가 모든 화면 경로를 담는지 |

새 기능을 넣고 `test_docs_coverage.py`가 실패하면, 실패 메시지에 나온 항목을 해당 문서에 적는다.

### smoke

| 파일 | 검사 |
|------|------|
| `test_imports.py` | 핵심 모듈 import (패키지 설치 환경에서) |

---

## 3. 실행

호스트 Python에는 의존성이 없으므로 **venv를 새로 만든다.**

```bash
# 저장소 루트에서
python -m venv .venv
.venv/Scripts/pip install -r requirements.docker.txt -r tests/requirements-test.txt
.venv/Scripts/python -m pytest tests            # 전체 — 505 passed
```

```bash
pytest tests/structure -q             # 폴더 · 문서 검사만 (의존성 최소 — pytest 만 있으면 된다)
pytest tests/unit -q                  # 단위
pytest tests/smoke -q                 # import 스모크
pytest tests/unit/test_auth.py -q     # 파일 하나
pytest -k signup                      # 이름으로 고르기
```

OpenCV · numpy가 없으면 `test_effects` 등은 자동으로 건너뛴다.

### 언제 돌리나

| 시점 | 권장 |
|------|------|
| 커밋 전 | `pytest tests/structure tests/unit` |
| 문서 · README를 고친 뒤 | `pytest tests/structure` — 문서 등록 검사 |
| 백엔드 의존성 설치 후 | `pytest` 전체 |
| Docker 배포 전 | 전체 + `scripts/deploy_check.py` |
| 학습(`training/`) 전 | `structure` + 학습 데이터 계약 테스트 |

---

## 4. 테스트 추가 가이드

- 새 모듈을 만들면 `tests/unit/`에 대응 테스트를 둔다.
- API 테스트는 `unit/conftest.py`의 `api_env` fixture(메모리 DB 앱 + 메일 가로채기)를 쓴다.
- 모델 · 네트워크 · Docker가 필요한 부분은 가짜 객체로 바꾼다. 실제 모델이 꼭 필요하면 `importorskip`.
- 테스트용 계정 · 파일 · 컨테이너를 만들었다면 테스트가 끝날 때 지운다.
- E2E(실제 업로드 · YOLO 추론)는 모델 가중치가 있을 때 `scripts/experiments/`나 수동 체크리스트(`docs/vaildates/`)로 확인한다.

## 관련 문서

- [`docs/plan/TESTING.md`](../docs/plan/TESTING.md) — 테스트 전략
- [`docs/plan/PROJECT_STRUCTURE.md`](../docs/plan/PROJECT_STRUCTURE.md)
- [`docs/vaildates/`](../docs/vaildates/README.md) — 수동 체크리스트 · 실험 결과
- [`RUN.md`](../RUN.md) — 서버 기동

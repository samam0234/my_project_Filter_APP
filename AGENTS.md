# 컷앤킵 — 프로젝트 규칙 (AGENTS.md)

Grok / Codex / 호환 에이전트가 저장소 루트에서 자동 로드하는 **프로젝트 규칙**이다.

상세 스킬: [`.agents/skills/cutnkeep/SKILL.md`](.agents/skills/cutnkeep/SKILL.md)  
요약 복제: [`.agents/AGENTS.md`](.agents/AGENTS.md)

## 한눈에

| 항목 | 규칙 |
|------|------|
| 커밋 type/scope | **영어** (`feat`, `fix`, `backend` …) |
| 커밋 제목 요약 | **한국어** (`feat(tts): 음성 인식 추가`) — 영어 요약 금지 |
| 커밋 본문·바닥글 | **한국어** |
| 작업 브랜치 | `feature/*` 등 |
| 통합 브랜치 | `develop` / `main` 만 |
| 병합 | **`git merge --no-ff`** (FF 금지) |
| 커밋 기록 파일 | **`docs/branchs/commits/` 에 무조건** (`YYMMDD_HHMM_[id]_[name]_[branch].md`) — 커밋 전·후 생략 금지. `docs/commits/` 사용 금지 |
| 비전 | **YOLO26s-seg** (기본 s; 전환 안내 `docs/plan/YOLO26S_DEFAULT.md`) |
| LLM 기본 | Ollama `gemma4:e4b` (선택: `LLM_PROVIDER=lora` Qwen2.5-1.5B 어댑터) |
| 프롬프트 규격 | `backend/app/services/prompt_spec.py` — 서빙·LoRA 학습 공용. 바꾸면 LoRA 재학습 |
| 인스턴스 선택 | `backend/app/services/instance_selector.py` (위치·순서·개수·색 규칙) |
| 계정 · 접근 | `/api/v1/auth/*` · `core/access.py` — 비로그인 처리·다운로드만(저장 없음), 기록·피드백·배치는 회원 본인 것만, 콘솔 API loopback |
| OpenCV 위치 | `backend/app/services/image_processor.py`, `effects.py` |
| Python 의존성 | 루트 `requirements.txt` / `requirements.docker.txt` |
| 학습 구역 | `training/` (YOLO detect/seg, LoRA) — 추론과 분리 |
| 테스트 | `tests/` + `pytest` — 실행 전 `docs/plan/TESTING.md` |
| 현재 스택 스냅샷 | `docs/plan/CURRENT_STACK.md` (포트·DB·Docker·제외 항목) |

## 커밋 제목 예시

```text
feat(tts): 음성 인식 추가     ✅
feat(llm): add to engine      ❌ (요약 영어 금지)
```

상세: `docs/guidance/commit-message.md`

## 실행

- 가이드: [`RUN.md`](./RUN.md)  
- console: `cd console && npm install && npm run dev` (5174)  
- backend: Python **3.11** venv + 루트 `requirements.txt` (3.14 비권장)

## 문서 허브

[`docs/README.md`](./docs/README.md)

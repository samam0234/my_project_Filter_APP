# 설명 사이트와 현재 숫자를 코드에 맞춤 / `f30bfac`

> 브랜치: `feature/docs-product-current`  
> 작성일: `2026-10-13 17:45`  
> 작성자: `agent`  
> 파일명: `261013_1745_f30bfac_docs-product-current_feature-docs-product-current.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(handover): 설명 사이트와 현재 숫자를 코드에 맞춤` |
| **커밋 번호 (SHA)** | `f30bfac7565f67fb39da15fba29b4a14b217410c` |
| **짧은 SHA** | `f30bfac` |
| **브랜치** | `feature/docs-product-current` |
| **부모 커밋** | `7ce1a25` |

## 2. 주 커밋 내용

- 인수인계 10절에 설명 사이트 `Portfolio/`를 제품과 분리해 적었다.
- 기능 목록에 설명 사이트와 제품 Chroma 경로를 보탰다.
- 테스트 505 · 95 · 21은 2026-10-12 기록으로 고정하고, 2026-10-10의 463 · 65 · 21을 현재 숫자로 두지 않았다.
- 테스트 README의 저장소 경로를 실제 경로로 고쳤다.

## 3. 상세 내용

### 3.1 배경 / 목적
제품 정본 문서가 설명 사이트, 깊이 추론 표, UTC+9, 모델 버튼을 빠뜨리거나 옛 테스트 숫자를 현재인 것처럼 적고 있었다.

### 3.2 변경 범위
- 추가된 경로: 없음
- 수정된 경로: `docs/HANDOVER.md`, `docs/FEATURES.md`, `docs/README.md`, `docs/plan/CURRENT_STACK.md`, `docs/plan/TESTING.md`, `tests/README.md`, `AGENTS.md`, `.agents/AGENTS.md`, `.agents/skills/cutnkeep/SKILL.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트
깊이 추론 표는 `deep_day`다. 날짜는 UTC+9다. 0회 안내 문장은 화면 상수와 같다. 안내 Chroma와 제품 Chroma는 다른 폴더다. 설명 사이트는 이미지를 처리하지 않는다.

### 3.4 의도적으로 하지 않은 것
테스트 재실행, 제품 코드 변경, 설명 마크다운 본문, 과거 커밋 기록의 당시 숫자 수정, 서버 배포.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [ ] API/UI 스모크
- 결과 서술: 문서를 코드의 표 이름, 모델 버튼, 횟수 프록시, 테스트 기록 날짜와 대조했다. 테스트를 다시 돌리지는 않았다.

### 4.2 부작용 / 리스크
테스트 건수는 2026-10-12 스냅샷이다. 그 뒤 테스트가 늘었다면 이 숫자는 다시 세야 한다.

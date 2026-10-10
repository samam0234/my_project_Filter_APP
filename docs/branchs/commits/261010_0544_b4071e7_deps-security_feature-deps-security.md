# 알려진 취약점이 있던 Python 의존성 9개를 고친 판으로 — pip-audit 0건 / `b4071e702f39308ac3bf53e80441f97aff581b53`

> 브랜치: `feature/deps-security`  
> 작성일: `2026-10-10 05:44`  
> 작성자: `agent`  
> 파일명: `261010_0544_b4071e7_deps-security_feature-deps-security.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(deps): 알려진 취약점이 있던 Python 의존성 9개를 고친 판으로 — pip-audit 0건` |
| **커밋 번호 (SHA)** | `b4071e702f39308ac3bf53e80441f97aff581b53` |
| **짧은 SHA** | `b4071e7` |
| **브랜치** | `feature/deps-security` |
| **부모 커밋** | `956a6b3` |

## 2. 주 커밋 내용

- `requirements.docker.txt` · `requirements.txt` 보안 업데이트 (9개 패키지)

## 3. 상세 내용

### 3.1 배경 / 목적
문서 전체 정리 중 보안 점검표의 "의존성 취약점 점검 안 함"을 실제로 돌렸더니 업로드 · 이미지 해석 · 웹 서버 쪽에 알려진 취약점이 있었다.

### 3.2 변경 범위
- 수정: `requirements.docker.txt`, `requirements.txt`

### 3.3 기술 포인트
- 코드는 langgraph(StateGraph · END) · langchain_core(Runnable) 만 써서 1.x 로 올려도 API 변경 없음
- 학습 venv 를 같은 판으로 올려 전체 테스트, Docker 이미지 재빌드로 실제 경로 확인

### 3.4 의도적으로 하지 않은 것
- npm 개발 도구 강제 업그레이드 (`npm audit fix --force`)
- GPU 이미지 재빌드 (다음 `up --build` 때 같은 파일로 빌드됨)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] pip-audit 0건, 테스트 451 통과, Docker 사진 처리 정상

### 4.2 부작용 / 리스크
- 학습 venv 패키지가 올라감 (이전 목록은 작업 중 백업)

### 4.3 후속 작업
- CI 에서 pip-audit 정기 실행

### 4.4 관련 문서
- `docs/guidance/security.md` 5절

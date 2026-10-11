# 포트폴리오 설명 문서 / `b1c697517059275e83ffaecc9ad957022928a2a0`

> 브랜치: `feature/portfolio`  
> 작성일: `2026-10-12 05:31`  
> 작성자: `agent`  
> 파일명: `261012_0531_b1c6975_portfolio-docs_feature-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `docs(portfolio): 컷앤킵 포트폴리오 설명 문서 추가` |
| **커밋 번호 (SHA)** | `b1c697517059275e83ffaecc9ad957022928a2a0` |
| **짧은 SHA** | `b1c6975` |
| **브랜치** | `feature/portfolio` |
| **부모 커밋** | `a25c7a7c037d453843a351a336b4bacc3f704c76` |

## 2. 주 커밋 내용

- 루트 `Portfolio/`에 설명 마크다운 9편과 목차 README를 추가함
- 같은 내용을 A4 Word `Portfolio/CutNKeep_Portfolio.docx`로 묶음
- Scribble의 ERD HTML·PNG와 스프레드시트 10개 시트를 `Portfolio/assets`로 옮김
- 기준은 2026-10-12 인수인계. 시트(2026-10-11)보다 뒤에 생긴 이메일 인증, AI 채팅, 실서버 운영을 구분해서 적음
- 제품 코드, 사이트, Flask는 이 커밋에 없음

## 3. 상세 내용

### 3.1 배경 / 목적

포트폴리오 사이트를 만들기 전에, 저장소 문서와 맞는 설명 문서를 먼저 고정하기 위함.
Scribble은 Git에 올라가지 않으므로 ERD와 시트를 Portfolio로 복사해야 사이트가 그 자료를 보여줄 수 있음.

### 3.2 변경 범위

- 추가된 경로: `Portfolio/**`, 이 기록, `docs/branchs/README.md` 목록 한 줄
- 수정된 경로: 없음 (제품 문서 수정 없음). README 목록은 이 기록 커밋
- 삭제된 경로: 없음

### 3.3 기술 포인트

- Word는 A4, Malgun Gothic, 제목 스타일, 표 너비 DXA, 머리글·쪽수. 스키마 검증은 UTF-8 모드에서 통과
- 스프레드시트 원본 xlsx는 커밋하지 않고 JSON으로 추출
- ERD HTML은 2026-10-11 모델 기준이라 `signup_pending`이 없다. 마크다운에 그 표를 따로 적음

### 3.4 의도적으로 하지 않은 것

- develop/main 병합, push, 배포
- Next.js 사이트와 Flask 안내 (다음 커밋)
- 제품 `.env`, 가중치, Scribble 원본 xlsx 커밋

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] Word 스키마 검증 통과 (`PYTHONUTF8=1`, `scripts/office/validate.py`)
- [ ] 로컬 사이트 실행 확인 — 아직 사이트가 없음
- [ ] Docker 확인 — 해당 없음
- 결과 서술: 문서 14개 파일, 커밋 `b1c6975`

### 4.2 부작용 / 리스크

설명 숫자는 실험 기록이라 모든 입력에서 재현되지 않는다.
시트와 인수인계의 테스트 수·배포 상태가 달라, 문서는 인수인계를 우선한다고 적어 두었다.

### 4.3 후속 작업

같은 `feature/portfolio`에 설명 사이트와 Flask 안내를 커밋한다. 병합은 사용자가 시킬 때만.

### 4.4 관련 문서

- `docs/HANDOVER.md`
- `docs/FEATURES.md`
- `Portfolio/README.md`

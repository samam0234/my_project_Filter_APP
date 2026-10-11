# 안내 챗 질문 추천과 화면 움직임 / `843aa1c88abae8cca61da26c115b19bae4041b8e`

> 브랜치: `feature/portfolio`  
> 작성일: `2026-10-12 06:17`  
> 작성자: `agent`  
> 파일명: `261012_0617_843aa1c_chat-suggest_feature-portfolio.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(portfolio): 안내 챗 질문 추천과 화면 움직임 추가` |
| **커밋 번호 (SHA)** | `843aa1c88abae8cca61da26c115b19bae4041b8e` |
| **짧은 SHA** | `843aa1c` |
| **브랜치** | `feature/portfolio` |
| **부모 커밋** | `6b1285a03b5d98a79c8c33a9a0d1a6499494207a` |

## 2. 주 커밋 내용

- 안내 챗 입력창 옆에 번개 버튼을 둠
- 번개를 누르면 프로젝트 질문 3개가 입력창 위에 나오고, 고르면 그 문장이 입력창에 들어감. 자동 전송은 하지 않음
- 왼쪽 기본 추천은 그대로 바로 질문함
- 화면 위의 「본문으로」 건너뛰기 버튼을 없앰
- 페이지 전환, 카드·이미지 호버, 읽기 줄, 홈의 안내 챗 상태 점을 넣음

## 3. 상세 내용

### 3.1 배경 / 목적

추천은 고정 버튼만 있어서 다른 질문을 고르기 어려웠고, 건너뛰기 버튼이 화면 위에 걸렸다.
페이지가 정적인 파일 서버처럼 보여서 읽는 움직임을 조금 넣기 위함.

### 3.2 변경 범위

- 수정: `Portfolio/site/app/chat/ChatPanel.tsx`, `globals.css`, `page.tsx`, `components/Shell.tsx`
- 추가: `Portfolio/site/components/GuideStatus.tsx`, `ReadingBar.tsx`
- 제품 코드와 Flask 안내는 이 커밋에 없음

### 3.3 기술 포인트

- 추천 질문은 문서에 있는 주제만 풀에 둠. 기록 키 `cnk-portfolio-chat-v1`은 그대로
- 움직임은 `prefers-reduced-motion`이면 끔

### 3.4 의도적으로 하지 않은 것

- develop/main 병합, push, 배포
- 안내 모델과 RAG 구조 변경

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] Edge에서 번개 → 질문 3개 → 클릭 시 입력창만 채워지고 전송되지 않음을 확인
- [x] 번개를 다시 누르면 다른 3개가 나옴
- [x] 홈과 챗 화면에 「본문으로」가 없음
- [ ] Docker 확인 — 해당 없음

### 4.2 부작용 / 리스크

개발 서버로 확인했다. 프로덕션 빌드는 이 커밋 이후 다시 돌려야 같은 화면이 된다.

### 4.3 후속 작업

안내 챗의 답변 품질은 별도 커밋에서 `Portfolio/ai`를 보강한다. 병합은 사용자가 시킬 때만.

### 4.4 관련 문서

- `Portfolio/site/README.md`

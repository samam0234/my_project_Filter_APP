# 깊이 추론 횟수가 보낼 때 줄어들게 수정 / `14f2cc20230902e38fc3d1ac103011d714591539`

> 브랜치: `feature/deep-quota-count`  
> 작성일: `2026-10-12 09:29`  
> 작성자: `agent`  
> 파일명: `261012_0929_14f2cc2_deep-quota-count_feature-deep-quota-count.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `fix(portfolio): 깊이 추론 횟수가 보낼 때 줄어들게 수정` |
| **커밋 번호 (SHA)** | `14f2cc20230902e38fc3d1ac103011d714591539` |
| **짧은 SHA** | `14f2cc2` |
| **브랜치** | `feature/deep-quota-count` |
| **부모 커밋** | `e9dcce1f2421a3b04568e43a42a9ac7646284d6d` |

## 2. 주 커밋 내용

- 뇌 버튼이 선택된 동안 보내기와 왼쪽 질문이 깊이 추론으로 나감
- 남은 횟수 배지는 답을 기다리기 전에 바로 하나 줄어듦
- 서버가 요청을 받으면 횟수를 확정하고, 답이 실패해도 되돌리지 않음
- 횟수 조회는 캐시하지 않고, 챗 응답에 남은 횟수를 실어 화면과 맞춤

## 3. 상세 내용

### 3.1 배경 / 목적

깊이 추론을 선택하고 질문을 보내도 배지가 `10/10`에 남는 경우가 있었다. 실패 응답은 횟수를 되돌려 줬고, 화면은 답이 끝난 뒤에야 서버 숫자를 다시 읽었다.

### 3.2 변경 범위

- 수정: `Portfolio/site/app/chat/ChatPanel.tsx`
- 수정: `Portfolio/site/app/api/chat/route.ts`
- 수정: `Portfolio/site/app/api/deep/route.ts`
- 수정: `Portfolio/site/lib/deepQuota.ts`
- 수정: `Portfolio/README.md`, `Portfolio/site/README.md`, `Portfolio/markdown/05-ai.md`

### 3.3 기술 포인트

- 예약된 횟수는 `done`으로 남긴다. 호출 실패로 `refunded` 처리하지 않는다
- 하루 10번을 넘기면 429이고 모델로 넘기지 않는다
- `GET /api/deep`와 챗 응답은 `Cache-Control: no-store`
- 브라우저가 연속으로 같은 질문을 여러 번 보내지 않도록 전송 중에는 다시 보내지 않는다
- 계정 구분이 없어 10번은 이 사이트 전체 기준이다. 한국 시간 오전 12시에 날짜가 바뀌면 초기화된다

### 3.4 의도적으로 하지 않은 것

- develop/main 병합과 push는 이 커밋에 넣지 않음
- 대화 본문을 SQLite에 저장하지 않음
- 제품 Ollama 기본 모델과 배포 설정은 바꾸지 않음

## 4. 커밋 관련 결과

### 4.1 동작 결과

- [x] 화면에서 깊이 추론을 보내기 전에 배지가 `9/10`에서 `8/10`으로 줄어듦
- [x] 왼쪽 질문도 뇌 버튼이 선택된 동안 `deep: true`로 나감
- [x] `GET /api/deep` 응답에 `Cache-Control: no-store`가 있음
- [x] 빈 messages 요청은 400
- [ ] Docker 확인 — 해당 없음

### 4.2 부작용 / 리스크

안내 서비스가 꺼져 있어도, 서버가 깊이 추론 요청을 받은 뒤에는 그 횟수가 남는다. 하루 10번을 실패로 모두 쓸 수 있다.

### 4.3 후속 작업

같은 요청에서 develop 병합, main 병합, push를 이어서 한다.

### 4.4 관련 문서

- `Portfolio/markdown/05-ai.md`
- `Portfolio/site/README.md`

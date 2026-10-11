# 프롬프트 가이드를 일반 가이드 / 에이전트에게 묻기로 나누고 AI 채팅 추가 / `2ad7ca5b01cd3894e074a861fd80343cf3d0a3f8`

> 브랜치: `feature/prompt-chat`  
> 작성일: `2026-10-11 21:42`  
> 작성자: `agent`  
> 파일명: `261011_2142_2ad7ca5_prompt-chat_feature-prompt-chat.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(guide): 프롬프트 가이드를 일반 가이드 / 에이전트에게 묻기로 나누고 AI 채팅 추가` |
| **커밋 번호 (SHA)** | `2ad7ca5b01cd3894e074a861fd80343cf3d0a3f8` |
| **짧은 SHA** | `2ad7ca5` |
| **브랜치** | `feature/prompt-chat` |
| **부모 커밋** | `bf646e7` |

## 2. 주 커밋 내용

- 프롬프트 가이드 두 구역: 일반 가이드(기존 그대로) / 에이전트에게 묻기(`?tab=agent`, AI 채팅)
- `POST /api/v1/chat` — Ollama `/api/chat`, 답변 모델 선택(작업실과 같은 목록)
- 답의 추천 문장 → "작업실에서 써 보기"

## 3. 상세 내용

### 3.1 배경 / 목적
사용자 지시: 프롬프트 가이드를 일반 가이드 / 에이전트에게 묻기로 나누고, AI 와 채팅하며 챗봇에서도 Ollama 모델을 고를 수 있게.

### 3.2 변경 범위
- 백엔드: `routers/chat.py` · `services/chat_agent.py` · `schemas/chat.py`(신규), `core/config.py`(CHAT_*) · `core/ratelimit.py` · `routers/router.py`
- 프런트: `components/chat/AgentChat.tsx` · `store/useChatStore.ts`(신규), `pages/GuidePage.tsx` · `ModelSelect.tsx` · `api/client.ts` · `types`
- 문서: API · FEATURES · user-frontend · frontend README · .env.example

### 3.3 기술 포인트
- 시스템 프롬프트는 서버 고정 · 서비스의 실제 기능만 기술 (없는 기능을 지어내지 않게), 요청의 system 역할은 422
- 대화는 서버에 저장하지 않고 화면이 최근 대화를 매번 보냄 (개인정보 비저장)
- `think:false` 로 생각 과정 출력 모델도 바로 답하게 (llama 로 오류 없음 확인), 제한 시간 최소 90초
- 실제 PC Ollama 로 e4b(10s) · 12b(16s) 답변 확인 — 추천 문장이 백틱으로 나옴

### 3.4 의도적으로 하지 않은 것
- 스트리밍 답변 (Cloudflare · nginx 버퍼링 이슈 — 후속)
- 대화 기록 저장

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 백엔드 pytest 505 · 프런트 vitest 95 · tsc 통과

### 4.2 부작용 / 리스크
- 큰 모델(27b) 첫 호출은 Cloudflare 주소에서 100초 제한에 걸릴 수 있음
- 로컬 `.env` 의 SMTP 값에 영향받던 메일 테스트를 독립으로 고침

### 4.3 후속 작업
- 전체 문서 갱신 → 병합 → 서버 배포

"""POST /chat — 프롬프트 가이드 "에이전트에게 묻기" (AI 채팅).

비로그인도 쓸 수 있다 (사용법 안내라 개인 데이터가 없다). 대신 무거운 호출이라 속도를 제한한다:
비로그인은 IP, 회원은 계정 기준 (CHAT_RATE_*). 서버는 대화를 저장하지 않는다 — 화면이 최근 대화를 함께 보낸다.
해석 모델은 작업실과 같은 목록에서 고른다 (llm_model — 설치되지 않았으면 400).
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.deps import current_user_optional
from app.core.ratelimit import chat_limiter, client_ip, enforce
from app.models.user import User
from app.routers.llm import resolve_model
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_agent

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, user: User | None = Depends(current_user_optional)) -> ChatResponse:
    settings = get_settings()
    if user is not None:
        enforce(chat_limiter, f"user:{user.id}", settings.chat_rate_member_per_min, "AI 상담 요청")
    else:
        enforce(
            chat_limiter, f"ip:{client_ip(request)}", settings.chat_rate_guest_per_min,
            "AI 상담 요청 (비로그인은 분당 제한이 더 낮습니다)",
        )
    model = resolve_model(body.llm_model)
    try:
        result = await run_in_threadpool(
            chat_agent.reply, [m.model_dump() for m in body.messages], model, settings
        )
    except chat_agent.ChatError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message) from exc
    return ChatResponse(reply=result.reply, model=result.model, elapsed_ms=result.elapsed_ms)

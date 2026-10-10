"""GET /llm/models — 작업실 "처리하기" 옆 모델 선택 상자의 내용.

비로그인도 볼 수 있다 (모델 이름 · 설치 여부뿐). 설치 여부는 10초 캐시라 호출이 가볍다.
설치되지 않은 모델은 `available=false` → 화면이 "미적용"으로 보여 주고 고를 수 없게 한다.
"""

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.services import llm_models

router = APIRouter(tags=["llm"])


@router.get("/llm/models")
async def list_llm_models() -> dict:
    """{enabled, reachable, default, models:[{id, label, available, default}]} — enabled=false 면 화면이 선택 상자를 숨긴다."""
    return await run_in_threadpool(llm_models.listing, get_settings())


def resolve_model(requested: str | None) -> str | None:
    """요청이 보낸 llm_model 을 확인해 쓸 모델 id 를 돌려준다 (사진 · GIF · 영상 라우터 공용). 안 되면 400."""
    from fastapi import HTTPException

    try:
        return llm_models.validate(requested, get_settings())
    except llm_models.ModelNotAvailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

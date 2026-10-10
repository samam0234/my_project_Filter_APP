"""문장 해석에 쓸 Ollama 모델 고르기 — 작업실 "처리하기" 옆 선택 상자의 서버 쪽.

사용자가 요청마다 해석 모델을 고를 수 있다 (사진 · GIF · 영상). 기본 모델은 `OLLAMA_MODEL` 이고, 고를 수 있는 목록은 아래 CATALOG 다.

  - 설치 여부는 Ollama 의 `GET /api/tags` 로 본다 (10초 캐시). **설치되지 않은 모델은 "미적용"** 으로 보이고 고를 수 없다.
    사용자가 `ollama pull <모델>` 로 내려받으면 다음 조회부터 자동으로 "미적용"이 사라진다 (서버 재시작 불필요).
  - 설정된 기본 모델은 Ollama 가 꺼져 있어도 항상 고를 수 있다 — 고르지 않았을 때와 똑같이 동작해야 하므로.
  - 큰 모델은 첫 호출에 모델을 올리느라 느리다 → 모델마다 해석 제한 시간(timeout_s)이 다르다.
  - `LLM_PROVIDER` 가 ollama 가 아니면(예: GPU 서버의 lora) 이 선택은 의미가 없다 — 목록은 `enabled=false` 로 내려 화면이 숨긴다.

고른 모델은 그 요청에만 적용된다 (서버 설정은 바뀌지 않는다): `with_model(settings, id)` 가 설정 복사본을 만든다.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from app.core.config import Settings

TAGS_TTL = 10.0  # 설치 목록 캐시 (초) — 새로 받은 모델이 "미적용"에서 빨리 풀리게 짧게


class ModelNotAvailable(ValueError):
    """고른 모델이 목록에 없거나 설치되어 있지 않다 (라우터가 400 으로 바꾼다)."""


@dataclass(frozen=True)
class LlmModel:
    id: str  # Ollama 모델 이름 (ollama list 의 NAME)
    label: str  # 화면에 보일 이름
    timeout_s: Optional[float] = None  # 해석 제한 시간 — None 이면 LLM_TIMEOUT_SECONDS
    note: str = ""  # 고를 때 화면에 보일 안내 (느린 모델 등)


CATALOG: tuple[LlmModel, ...] = (
    LlmModel("gemma4:e4b", "Ollama e4b"),
    LlmModel("gemma4:12b", "Ollama 12b", timeout_s=90.0, note="e4b 보다 정확할 수 있어요. 처음 한 번은 모델을 올리느라 수십 초 걸려요."),
    LlmModel(
        "qwen3.8:27b", "Qwen 3.8 · 27b", timeout_s=180.0,
        note="가장 큰 모델이에요. GPU 메모리가 모자라면 일부를 CPU 로 돌려 처음 한 번은 3분 가까이, 이후에도 1분쯤 걸려요.",
    ),
)

_lock = threading.Lock()
_cache: tuple[float, Optional[frozenset[str]]] = (0.0, None)


def catalog(settings: Settings) -> list[LlmModel]:
    """고를 수 있는 모델 — 설정된 기본 모델이 목록에 없으면 맨 앞에 넣는다 (OLLAMA_MODEL 을 바꿔 쓰는 경우)."""
    items = list(CATALOG)
    if settings.ollama_model not in {m.id for m in items}:
        items.insert(0, LlmModel(settings.ollama_model, settings.ollama_model))
    return items


def installed(settings: Settings, *, force: bool = False) -> Optional[frozenset[str]]:
    """Ollama 에 설치된 모델 이름. Ollama 에 닿지 않으면 None."""
    global _cache
    now = time.monotonic()
    with _lock:
        stamp, names = _cache
        if not force and now - stamp < TAGS_TTL:
            return names
    base = (settings.llm_base_url or "http://localhost:11434").rstrip("/")
    names = None
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        names = frozenset(m.get("name") or m.get("model") or "" for m in data.get("models", []))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("Ollama 설치 모델 조회 실패 ({}): {}", base, exc)
    with _lock:
        _cache = (now, names)
    return names


def is_enabled(settings: Settings) -> bool:
    """모델 고르기가 의미가 있는지 — 해석을 Ollama 가 맡을 때만."""
    return (settings.llm_provider or "").strip().lower() == "ollama"


def listing(settings: Settings) -> dict:
    """GET /llm/models 응답: 화면의 선택 상자 내용."""
    names = installed(settings)
    models = []
    for m in catalog(settings):
        is_default = m.id == settings.ollama_model
        # 기본 모델은 Ollama 가 꺼져 있어도 고를 수 있다 (고르지 않았을 때와 같은 동작)
        available = is_default or (names is not None and m.id in names)
        models.append({"id": m.id, "label": m.label, "available": available, "default": is_default, "note": m.note})
    return {"enabled": is_enabled(settings), "reachable": names is not None, "default": settings.ollama_model, "models": models}


def validate(requested: Optional[str], settings: Settings) -> Optional[str]:
    """요청이 보낸 모델 이름을 확인해 쓸 모델 id 를 돌려준다. 안 골랐거나 기본이면 None(= 설정 그대로)."""
    if not requested or not requested.strip():
        return None
    requested = requested.strip()
    if not is_enabled(settings):
        return None  # 해석을 Ollama 가 안 맡는다 — 선택은 효과가 없으니 조용히 무시
    if requested == settings.ollama_model:
        return None
    if requested not in {m.id for m in catalog(settings)}:
        raise ModelNotAvailable(f"지원하지 않는 모델입니다: {requested}")
    names = installed(settings, force=True)  # 막 내려받은 모델이 바로 되게 — 요청 때는 캐시를 쓰지 않는다
    if names is None:
        raise ModelNotAvailable("Ollama 에 연결할 수 없어 다른 모델을 쓸 수 없습니다. 기본 모델로 처리해 주세요.")
    if requested not in names:
        raise ModelNotAvailable(f"{requested} 모델이 설치되어 있지 않습니다 (미적용). ollama pull {requested} 로 내려받으면 쓸 수 있어요.")
    return requested


def with_model(settings: Settings, model_id: Optional[str]) -> Settings:
    """이 요청에서만 쓸 설정 복사본 — 모델 이름과 해석 제한 시간을 바꾼다. model_id 가 없으면 원본 그대로."""
    if not model_id:
        return settings
    update: dict = {"ollama_model": model_id}
    for m in CATALOG:
        if m.id == model_id and m.timeout_s:
            update["llm_timeout_seconds"] = max(settings.llm_timeout_seconds, m.timeout_s)
    return settings.model_copy(update=update)

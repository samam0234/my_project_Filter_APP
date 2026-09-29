"""LLM 프롬프트 분석: 자연어 → ParsedPrompt JSON.

prompt_analyzer 노드가 호출한다. provider 는 Settings.llm_provider:
  - ollama  : 로컬 Ollama native /api/chat (기본, gemma4:e4b)
  - openai  : Chat Completions (json_object 모드)
  - gemini  : generateContent (application/json 응답)
  - lora    : training/lora 어댑터를 프로세스 안에서 추론 (services/prompt_lora)
  - heuristic / 빈 값 : LLM 생략 → None 반환 (호출측이 휴리스틱 사용)

원칙:
  - 외부 의존성 없이 표준 라이브러리 urllib 만 사용 (Docker 경량 이미지 호환)
  - 실패는 전부 LLMError 로 올린다 → nodes 에서 휴리스틱 fallback
  - OpenCV / YOLO 호출 금지 (텍스트 구조화만 담당)
  - 지시문·정규화 규격은 services/prompt_spec.py (LoRA 학습과 공용)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import Settings, get_settings
from app.schemas.request import ParsedPrompt
from app.services.prompt_spec import (  # noqa: F401  (테스트·호출측 재노출)
    ALLOWED_EFFECTS,
    SYSTEM_PROMPT,
    LLMError,
    extract_json_object,
    normalize_parsed,
)

LLM_PROVIDERS = {"ollama", "openai", "gemini", "lora"}

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """JSON POST → JSON 응답 dict. 네트워크/HTTP/디코드 오류는 LLMError."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise LLMError(f"HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LLMError(f"연결 실패: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LLMError(f"응답 JSON 디코드 실패: {exc}") from exc


def _call_ollama(prompt: str, settings: Settings) -> str:
    """Ollama native /api/chat (format=json, 비스트리밍)."""
    base = (settings.llm_base_url or "http://localhost:11434").rstrip("/")
    data = _post_json(
        f"{base}/api/chat",
        {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=settings.llm_timeout_seconds,
    )
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise LLMError(f"Ollama 응답 형식 오류: {data!r:.300}") from exc


def _call_openai(prompt: str, settings: Settings) -> str:
    """OpenAI Chat Completions (response_format=json_object)."""
    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY 미설정")
    data = _post_json(
        OPENAI_CHAT_URL,
        {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        timeout=settings.llm_timeout_seconds,
    )
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"OpenAI 응답 형식 오류: {data!r:.300}") from exc


def _call_gemini(prompt: str, settings: Settings) -> str:
    """Gemini generateContent (responseMimeType=application/json)."""
    if not settings.gemini_api_key:
        raise LLMError("GEMINI_API_KEY 미설정")
    data = _post_json(
        GEMINI_URL_TEMPLATE.format(model=settings.gemini_model),
        {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0,
            },
        },
        headers={"x-goog-api-key": settings.gemini_api_key},
        timeout=settings.llm_timeout_seconds,
    )
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Gemini 응답 형식 오류: {data!r:.300}") from exc


_CALLERS = {
    "ollama": _call_ollama,
    "openai": _call_openai,
    "gemini": _call_gemini,
}


def llm_enabled(settings: Settings | None = None) -> bool:
    """provider 가 실제 LLM(ollama/openai/gemini)인지."""
    settings = settings or get_settings()
    return (settings.llm_provider or "").strip().lower() in LLM_PROVIDERS


def parse_prompt_llm(
    prompt: str,
    settings: Settings | None = None,
) -> Optional[ParsedPrompt]:
    """LLM 으로 프롬프트 구조화.

    반환:
      - ParsedPrompt : 성공
      - None         : provider 가 heuristic/빈 값/미지원 → LLM 생략
    예외:
      - LLMError     : 호출·파싱 실패 (호출측이 휴리스틱으로 fallback)
    """
    settings = settings or get_settings()
    provider = (settings.llm_provider or "").strip().lower()
    if provider in {"", "heuristic", "none"}:
        return None
    if provider == "lora":
        # 로컬 어댑터 — HTTP 가 아니라 프로세스 내 추론 (services/prompt_lora)
        from app.services.prompt_lora import parse_prompt_lora

        return parse_prompt_lora(prompt, settings)
    caller = _CALLERS.get(provider)
    if caller is None:
        logger.warning("알 수 없는 LLM_PROVIDER={} — 휴리스틱 사용", provider)
        return None

    text = caller(prompt, settings)
    return normalize_parsed(extract_json_object(text))

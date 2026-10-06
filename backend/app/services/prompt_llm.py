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
from contextvars import ContextVar
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
# 이번 호출에서 실제로 성공한 provider. 노드가 휴리스틱과 구분하려고 읽는다.
_LAST_PROVIDER: ContextVar[str] = ContextVar("cutnkeep_llm_provider", default="")

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


def _call_ollama(prompt: str, settings: Settings, system: str = SYSTEM_PROMPT) -> str:
    """Ollama native /api/chat (format=json, 비스트리밍)."""
    base = (settings.llm_base_url or "http://localhost:11434").rstrip("/")
    data = _post_json(
        f"{base}/api/chat",
        {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
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


def _call_openai(prompt: str, settings: Settings, system: str = SYSTEM_PROMPT) -> str:
    """OpenAI Chat Completions (response_format=json_object)."""
    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY 미설정")
    data = _post_json(
        OPENAI_CHAT_URL,
        {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
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


def _call_gemini(prompt: str, settings: Settings, system: str = SYSTEM_PROMPT) -> str:
    """Gemini generateContent (responseMimeType=application/json)."""
    if not settings.gemini_api_key:
        raise LLMError("GEMINI_API_KEY 미설정")
    data = _post_json(
        GEMINI_URL_TEMPLATE.format(model=settings.gemini_model),
        {
            "systemInstruction": {"parts": [{"text": system}]},
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
    """provider 가 실제 LLM(ollama/openai/gemini/lora)인지."""
    settings = settings or get_settings()
    return (settings.llm_provider or "").strip().lower() in LLM_PROVIDERS


def clear_last_llm_provider() -> None:
    """직전 호출의 provider 기록을 지운다. 노드가 호출 직전에 쓴다."""
    _LAST_PROVIDER.set("")


def last_llm_provider() -> str:
    """방금 성공한 provider. 없으면 빈 문자열."""
    return _LAST_PROVIDER.get()


def llm_chain(settings: Settings | None = None) -> list[str]:
    """기본 provider 와, 다르면 LLM_FALLBACK 한 단계.

    heuristic·빈 값·알 수 없는 이름은 체인을 만들지 않는다 (LLM 생략).
    """
    settings = settings or get_settings()
    primary = (settings.llm_provider or "").strip().lower()
    if primary not in LLM_PROVIDERS:
        return []
    chain = [primary]
    fallback = (settings.llm_fallback or "").strip().lower()
    if fallback in LLM_PROVIDERS and fallback not in chain:
        chain.append(fallback)
    return chain


def _parse_with_provider(
    provider: str,
    prompt: str,
    settings: Settings,
    examples: str,
) -> ParsedPrompt:
    """provider 하나. 실패는 LLMError."""
    if provider == "lora":
        from app.services.prompt_lora import parse_prompt_lora

        return parse_prompt_lora(prompt, settings)
    caller = _CALLERS.get(provider)
    if caller is None:
        raise LLMError(f"지원하지 않는 provider: {provider}")
    text = caller(prompt, settings, SYSTEM_PROMPT + examples)
    return normalize_parsed(extract_json_object(text))


def parse_prompt_llm(
    prompt: str,
    settings: Settings | None = None,
    examples: str = "",
) -> Optional[ParsedPrompt]:
    """LLM 으로 프롬프트 구조화.

    examples: RAG 가 찾은 비슷한 정답 예시 블록 (services/prompt_rag.format_examples).
              SYSTEM_PROMPT 뒤에 붙인다. lora 는 학습 템플릿이 고정이라 쓰지 않는다.

    기본 provider 가 LLMError 이면 LLM_FALLBACK 을 한 번 더 시도한다.
    성공한 이름은 last_llm_provider() 에 남는다.

    반환:
      - ParsedPrompt : 성공
      - None         : provider 가 heuristic/빈 값/미지원 → LLM 생략
    예외:
      - LLMError     : 체인 전부 실패 (호출측이 휴리스틱으로 fallback)
    """
    settings = settings or get_settings()
    clear_last_llm_provider()
    chain = llm_chain(settings)
    if not chain:
        provider = (settings.llm_provider or "").strip().lower()
        if provider not in {"", "heuristic", "none"}:
            logger.warning("알 수 없는 LLM_PROVIDER={} — 휴리스틱 사용", provider)
        return None

    errors: list[str] = []
    for index, provider in enumerate(chain):
        try:
            parsed = _parse_with_provider(provider, prompt, settings, examples)
        except LLMError as exc:
            errors.append(f"{provider}: {exc}")
            logger.warning("LLM {} 실패: {}", provider, exc)
            continue
        _LAST_PROVIDER.set(provider)
        if index:
            logger.warning("LLM fallback 성공 provider={}", provider)
        return parsed
    raise LLMError(" | ".join(errors))


def parse_prompt_or_heuristic(
    prompt: str,
    settings: Settings | None = None,
) -> ParsedPrompt:
    """배치·영상용. LLM 체인이 실패하거나 꺼져 있으면 휴리스틱."""
    from app.workflows.nodes import parse_prompt_heuristic

    try:
        parsed = parse_prompt_llm(prompt, settings)
        if parsed is not None:
            return parsed
    except Exception as exc:
        logger.warning("프롬프트 LLM 실패 — 휴리스틱: {}", exc)
    return parse_prompt_heuristic(prompt)

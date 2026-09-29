"""LLM 프롬프트 분석: 자연어 → ParsedPrompt JSON.

prompt_analyzer 노드가 호출한다. provider 는 Settings.llm_provider:
  - ollama  : 로컬 Ollama native /api/chat (기본, gemma4:e4b)
  - openai  : Chat Completions (json_object 모드)
  - gemini  : generateContent (application/json 응답)
  - heuristic / 빈 값 : LLM 생략 → None 반환 (호출측이 휴리스틱 사용)

원칙:
  - 외부 의존성 없이 표준 라이브러리 urllib 만 사용 (Docker 경량 이미지 호환)
  - 실패는 전부 LLMError 로 올린다 → nodes 에서 휴리스틱 fallback
  - OpenCV / YOLO 호출 금지 (텍스트 구조화만 담당)
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import Settings, get_settings
from app.schemas.request import ParsedPrompt

ALLOWED_EFFECTS = {"remove_bg", "blur", "crop", "none"}
LLM_PROVIDERS = {"ollama", "openai", "gemini"}

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

# 【수동·튜닝】 시스템 프롬프트 — target 어휘는 YOLO names(COCO) 와 맞춘다.
# 커스텀 학습 클래스를 추가하면 여기 어휘 목록도 같이 늘릴 것.
SYSTEM_PROMPT = """You convert an image-editing request (Korean or English) into JSON.
The app keeps only the requested objects and edits the background.

Return ONLY a JSON object with exactly these keys:
{"target": [string], "effect": string, "intensity": integer, "crop": boolean}

Rules:
- target: objects to KEEP, as lowercase English COCO class names, e.g.
  person, dog, cat, car, bag -> use "handbag" or "backpack", cup, bottle, chair,
  bicycle, motorcycle, bird, horse, laptop, cell phone, teddy bear.
  Map synonyms to the class name (puppy/강아지 -> dog, 사람/인물 -> person, 폰 -> cell phone).
  If no object is mentioned, use ["person"].
- effect: one of "remove_bg" (make background transparent, default),
  "blur" (blur only the background), "crop" (cut out around the object), "none".
- intensity: blur strength 0-100. Use a number from the request if given, else 15.
- crop: true if the user also asks to crop/trim around the object, else false.

Examples:
"강아지만 남기고 배경 블러" -> {"target": ["dog"], "effect": "blur", "intensity": 15, "crop": false}
"사람이랑 고양이 빼고 배경 지워줘" -> {"target": ["person", "cat"], "effect": "remove_bg", "intensity": 15, "crop": false}
"keep the car, blur background strength 40 and crop" -> {"target": ["car"], "effect": "blur", "intensity": 40, "crop": true}"""


class LLMError(RuntimeError):
    """LLM 호출·응답 파싱 실패. 호출측은 휴리스틱으로 fallback 한다."""


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


def extract_json_object(text: str) -> Dict[str, Any]:
    """LLM 텍스트에서 JSON 객체 추출. ```json 코드펜스·앞뒤 잡음 허용."""
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError(f"JSON 객체 없음: {text[:200]!r}")
        text = text[start : end + 1]
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"JSON 파싱 실패: {exc}") from exc
    if not isinstance(obj, dict):
        raise LLMError("JSON 최상위가 객체가 아님")
    return obj


def normalize_parsed(raw: Dict[str, Any]) -> ParsedPrompt:
    """LLM JSON → ParsedPrompt. 값 범위·어휘를 스키마에 맞게 보정한다.

    - target: 문자열/리스트 허용 → 소문자·공백 정리·중복 제거, 비면 LLMError
    - effect: 허용 목록 밖이면 LLMError (휴리스틱이 더 믿을 만함)
    - intensity: 숫자 변환 후 0~100 클램프, 실패 시 15
    - crop: effect=crop 이면 True 로 맞춤 (휴리스틱과 동일 규칙)
    """
    targets_raw = raw.get("target", raw.get("targets"))
    if isinstance(targets_raw, str):
        targets_raw = [targets_raw]
    if not isinstance(targets_raw, list):
        raise LLMError(f"target 형식 오류: {targets_raw!r}")
    targets: list[str] = []
    for t in targets_raw:
        if not isinstance(t, str):
            continue
        name = " ".join(t.lower().replace("_", " ").split())
        if name and name not in targets:
            targets.append(name)
    if not targets:
        raise LLMError("target 비어 있음")

    effect = str(raw.get("effect") or "remove_bg").strip().lower()
    if effect not in ALLOWED_EFFECTS:
        raise LLMError(f"허용되지 않은 effect: {effect!r}")

    try:
        intensity = int(float(raw.get("intensity", 15)))
    except (TypeError, ValueError):
        intensity = 15
    intensity = max(0, min(100, intensity))

    crop_raw = raw.get("crop", False)
    if isinstance(crop_raw, str):
        crop = crop_raw.strip().lower() in {"true", "1", "yes"}
    else:
        crop = bool(crop_raw)
    if effect == "crop":
        crop = True

    return ParsedPrompt(target=targets, effect=effect, intensity=intensity, crop=crop)


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
    caller = _CALLERS.get(provider)
    if caller is None:
        logger.warning("알 수 없는 LLM_PROVIDER={} — 휴리스틱 사용", provider)
        return None

    text = caller(prompt, settings)
    return normalize_parsed(extract_json_object(text))

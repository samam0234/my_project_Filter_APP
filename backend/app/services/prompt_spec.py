"""프롬프트 → ParsedPrompt 변환 규격 (서비스 LLM · LoRA 학습 공용).

- SYSTEM_PROMPT        : LLM 지시문 + 스키마 + few-shot (Ollama/OpenAI/Gemini/LoRA 동일)
- extract_json_object  : LLM 텍스트에서 JSON 객체 추출
- normalize_parsed     : JSON → ParsedPrompt (어휘·범위 보정)

settings·HTTP 의존이 없어 training/lora 에서도 그대로 import 한다.
규격을 바꾸면 서비스와 학습 데이터가 함께 바뀌므로 LoRA 재학습이 필요하다.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.schemas.request import EFFECTS, POSITIONS, InstanceSelector, ParsedPrompt


class LLMError(RuntimeError):
    """LLM 호출·응답 파싱 실패. 호출측은 휴리스틱으로 fallback 한다."""


ALLOWED_EFFECTS = set(EFFECTS)

# 【수동·튜닝】 시스템 프롬프트 — target 어휘는 YOLO names(COCO) 와 맞춘다.
# 커스텀 학습 클래스를 추가하면 여기 어휘 목록도 같이 늘릴 것.
SYSTEM_PROMPT = """You convert an image-editing request (Korean or English) into JSON.

Return ONLY a JSON object with exactly these keys:
{"target": [string], "effect": string, "intensity": integer, "crop": boolean,
 "selector": null or {"position": string or null, "rank": integer or null, "count": integer or null, "attributes": [string]}}

target: object classes the request is about, as lowercase English COCO class names, e.g.
  person, dog, cat, car, bus, truck, bicycle, motorcycle, bird, horse, cup, bottle, chair,
  laptop, cell phone, handbag, backpack, teddy bear.
  Map synonyms to the class name (강아지/puppy -> dog, 사람/남자/여자/아이/man/woman -> person,
  폰 -> cell phone, 머그컵 -> cup). If no object is mentioned, use ["person"].

effect — decide whether the target objects are KEPT or ERASED:
  "remove_bg"     keep the target, make everything else transparent (default).
                  "X만 남기고 배경 제거", "X 빼고/제외하고 전부 지워" -> keep X -> remove_bg
  "blur"          keep the target sharp, blur the rest.
  "crop"          keep the target, cut the image around it.
  "none"          no visual change.
  "remove_object" ERASE the target object itself and fill the hole with background.
                  "X 지워줘", "X 없애줘", "remove the X", "erase X" -> remove_object
  Removing the BACKGROUND is remove_bg, never remove_object.

intensity: blur strength 0-100. Use a number from the request if given, else 15.
crop: true if the user also asks to crop/trim around the object, else false.

selector — which instances of the target class, when the request points at specific ones:
  position: "front" (맨 앞/앞쪽/closest), "back" (맨 뒤), "left" (왼쪽), "right" (오른쪽),
            "center" (가운데/중앙), "largest" (가장 큰), "smallest" (가장 작은), or null.
  rank:     1-based order along that position. "오른쪽에서 두 번째" -> position "right", rank 2.
            null for the first one.
  count:    only when the request states a number: "한 명"/"one" -> 1, "두 사람"/"two" -> 2.
            With a position word, count is 1. Otherwise null (a noun alone like "남자"
            or "the woman" does not set count — Korean nouns do not mark singular/plural).
  attributes: short lowercase English "color part" phrases describing the instance,
            e.g. "red helmet", "neon yellow vest", "blue shirt", "white car". [] if none.
            For people use part words helmet, hat, vest, shirt, jacket, pants, shoes.
            For objects use "color class", e.g. "black car", "red bus".
  Use null for selector when the request means ALL instances of the target class.

Examples:
"강아지만 남기고 배경 블러" -> {"target": ["dog"], "effect": "blur", "intensity": 15, "crop": false, "selector": null}
"사람이랑 고양이 빼고 배경 지워줘" -> {"target": ["person", "cat"], "effect": "remove_bg", "intensity": 15, "crop": false, "selector": null}
"맨 앞에 빨간 안전모와 형광 조끼를 입은 남자를 제외하고 전부 제거" -> {"target": ["person"], "effect": "remove_bg", "intensity": 15, "crop": false, "selector": {"position": "front", "rank": null, "count": 1, "attributes": ["red helmet", "neon yellow vest"]}}
"왼쪽에서 두 번째 사람 지워줘" -> {"target": ["person"], "effect": "remove_object", "intensity": 15, "crop": false, "selector": {"position": "left", "rank": 2, "count": 1, "attributes": []}}
"흰색 차 없애줘" -> {"target": ["car"], "effect": "remove_object", "intensity": 15, "crop": false, "selector": {"position": null, "rank": null, "count": null, "attributes": ["white car"]}}
"keep the biggest dog and blur background strength 40" -> {"target": ["dog"], "effect": "blur", "intensity": 40, "crop": false, "selector": {"position": "largest", "rank": null, "count": 1, "attributes": []}}"""


def extract_json_object(text: str) -> Dict[str, Any]:
    """LLM 텍스트에서 JSON 객체 추출. ```json 코드펜스·앞뒤 잡음 허용."""
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
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


def _clean_phrase(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


def normalize_selector(raw: Any) -> Optional[InstanceSelector]:
    """selector JSON → InstanceSelector. 잘못된 값은 버리고(None) 전체를 실패시키지 않는다.

    선택자는 보조 조건이라, 일부가 틀려도 target/effect 는 살린다.
    """
    if not isinstance(raw, dict):
        return None
    position = raw.get("position")
    position = _clean_phrase(position) if isinstance(position, str) else None
    if position not in POSITIONS:
        position = None

    def _int_1_50(value: Any) -> Optional[int]:
        try:
            n = int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
        return n if n is not None and 1 <= n <= 50 else None

    count = _int_1_50(raw.get("count"))
    rank = _int_1_50(raw.get("rank"))
    if rank == 1:
        rank = None  # 첫 번째는 기본값과 같음

    attrs_raw = raw.get("attributes") or []
    if isinstance(attrs_raw, str):
        attrs_raw = [attrs_raw]
    attributes: List[str] = []
    if isinstance(attrs_raw, list):
        for a in attrs_raw:
            if isinstance(a, str) and _clean_phrase(a) and _clean_phrase(a) not in attributes:
                attributes.append(_clean_phrase(a))
    selector = InstanceSelector(
        position=position, rank=rank, count=count, attributes=attributes[:5]
    )
    return None if selector.is_empty() else selector


def normalize_parsed(raw: Dict[str, Any]) -> ParsedPrompt:
    """LLM JSON → ParsedPrompt. 값 범위·어휘를 스키마에 맞게 보정한다.

    - target: 문자열/리스트 허용 → 소문자·공백 정리·중복 제거, 비면 LLMError
    - effect: 허용 목록 밖이면 LLMError (휴리스틱이 더 믿을 만함)
    - intensity: 숫자 변환 후 0~100 클램프, 실패 시 15
    - crop: effect=crop 이면 True 로 맞춤 (휴리스틱과 동일 규칙)
    - selector: normalize_selector (잘못된 부분만 버림)
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
        name = _clean_phrase(t)
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

    return ParsedPrompt(
        target=targets,
        effect=effect,
        intensity=intensity,
        crop=crop,
        selector=normalize_selector(raw.get("selector")),
    )


# =============================================================================
# LoRA 어댑터 규격 (training/lora 학습 · services/prompt_lora 서빙 공용)
# -----------------------------------------------------------------------------
# 작은 모델(Qwen2.5-1.5B)은 긴 SYSTEM_PROMPT 대신 짧은 지시 + 학습으로 규격을 익힌다.
# 이 템플릿이나 parsed_to_json 형식을 바꾸면 어댑터를 다시 학습해야 한다.
# =============================================================================
LORA_TEMPLATE = """### 지시
컷앤킵 이미지 편집 요청을 JSON 한 줄로 변환하세요.
스키마: {{"target":[COCO 클래스 소문자],"effect":"remove_bg|blur|crop|none|remove_object","intensity":0-100,"crop":bool,"selector":null|{{"position":"front|back|left|right|center|largest|smallest"|null,"rank":int|null,"count":int|null,"attributes":["색 부위"]}}}}
remove_object 는 대상을 지우고, 나머지 effect 는 대상을 남긴다.

### 프롬프트
{prompt}

### 응답
{response}"""


def parsed_to_json(parsed: ParsedPrompt) -> str:
    """정답 JSON 한 줄 (키 순서 고정). LoRA 학습 레이블과 평가 비교에 사용."""
    selector = None
    if parsed.selector is not None and not parsed.selector.is_empty():
        selector = {
            "position": parsed.selector.position,
            "rank": parsed.selector.rank,
            "count": parsed.selector.count,
            "attributes": list(parsed.selector.attributes),
        }
    payload = {
        "target": list(parsed.target),
        "effect": parsed.effect,
        "intensity": parsed.intensity,
        "crop": parsed.crop,
        "selector": selector,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

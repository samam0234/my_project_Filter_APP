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
  폰 -> cell phone, 머그컵 -> cup, 화분 -> potted plant, 꽃병 -> vase, 곰인형 -> teddy bear).
  Scenery / large regions are also valid targets (lowercase English): building, sky, road, sidewalk,
  tree, grass, water, mountain, wall, floor, ceiling, ground, bridge, fence.
  Map: 건물/빌딩/집/아파트/house -> building, 하늘 -> sky, 도로/차도 -> road, 인도/보도 -> sidewalk,
  나무/가로수 -> tree, 잔디/풀밭 -> grass, 바다/호수/강/물 -> water, 산 -> mountain, 벽 -> wall, 바닥 -> floor,
  천장 -> ceiling, 땅/모래/흙 -> ground, 울타리 -> fence. Use them only when the request is about that region.
  If no object is mentioned, use ["person"].

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
"건물만 남기고 배경 제거" -> {"target": ["building"], "effect": "remove_bg", "intensity": 15, "crop": false, "selector": null}
"하늘 빼고 전부 블러" -> {"target": ["sky"], "effect": "blur", "intensity": 15, "crop": false, "selector": null}
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


# =============================================================================
# 어휘 정규화 — LLM·LoRA 가 규격 밖 단어를 내도 서비스가 쓸 수 있는 값으로
# -----------------------------------------------------------------------------
# 확장 평가셋(seed/eval_ext.jsonl)에서 실제로 나온 이탈:
#   effect "keep" (Ollama) → 파싱 전체 실패 → 정확도 43% 키워드 파서로 떨어짐
#   target "flower pot" · "train car" · "pizza piece" (LoRA) → YOLO(COCO) 에 없는 이름이라 아무것도 못 찾음
# =============================================================================
COCO_CLASSES: frozenset[str] = frozenset({
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
    "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
})

# 배경 덩어리 — 사용자가 말하는 단위 → ADE20K(SegFormer) 클래스 이름들. COCO(YOLO)에 없는 대상은 이쪽이 맡는다
# (services/stuff_segmentation). 묶음 안의 클래스는 확률을 합쳐서 판정한다.
STUFF_GROUPS: dict[str, tuple[str, ...]] = {
    "building": ("building", "house", "skyscraper", "hovel"),
    "sky": ("sky",),
    "road": ("road",),
    "sidewalk": ("sidewalk",),
    "tree": ("tree", "palm"),
    "grass": ("grass",),
    "water": ("water", "sea", "river", "lake", "waterfall"),
    "mountain": ("mountain", "hill"),
    "wall": ("wall",),
    "floor": ("floor",),
    "ceiling": ("ceiling",),
    "ground": ("earth", "sand", "land"),
    "bridge": ("bridge",),
    "fence": ("fence",),
}
STUFF_CLASSES: frozenset[str] = frozenset(STUFF_GROUPS)

_STUFF_ALIASES: dict[str, str] = {
    **dict.fromkeys(("buildings", "건물", "빌딩", "건축물", "house", "houses", "집", "주택", "skyscraper", "skyscrapers",
                     "apartment", "아파트", "고층빌딩"), "building"),
    **dict.fromkeys(("skies", "하늘"), "sky"),
    **dict.fromkeys(("roads", "street", "streets", "도로", "차도", "asphalt"), "road"),
    **dict.fromkeys(("sidewalks", "pavement", "인도", "보도"), "sidewalk"),
    **dict.fromkeys(("trees", "palm", "forest", "나무", "가로수", "숲"), "tree"),
    **dict.fromkeys(("lawn", "meadow", "잔디", "잔디밭", "풀", "풀밭"), "grass"),
    **dict.fromkeys(("sea", "ocean", "lake", "river", "물", "바다", "호수", "강", "수면"), "water"),
    **dict.fromkeys(("mountains", "hill", "hills", "산", "산맥", "언덕"), "mountain"),
    **dict.fromkeys(("walls", "벽"), "wall"),
    **dict.fromkeys(("floors", "바닥", "마루"), "floor"),
    **dict.fromkeys(("ceilings", "천장"), "ceiling"),
    **dict.fromkeys(("sand", "earth", "land", "dirt", "땅", "지면", "모래", "흙"), "ground"),
    **dict.fromkeys(("bridges", "교량"), "bridge"),
    **dict.fromkeys(("fences", "울타리", "펜스"), "fence"),
}

# 규격 밖 이름 → COCO 클래스 (영어 변형 · 한국어 그대로 나온 경우)
TARGET_ALIASES: dict[str, str] = {
    **_STUFF_ALIASES,
    **dict.fromkeys(("people", "human", "man", "men", "woman", "women", "child", "children", "kid", "kids",
                     "boy", "girl", "baby", "worker", "workers", "pedestrian", "couple",
                     "사람", "남자", "여자", "아이"), "person"),
    **dict.fromkeys(("puppy", "puppies", "강아지", "개"), "dog"),
    **dict.fromkeys(("kitten", "고양이"), "cat"),
    **dict.fromkeys(("bike", "자전거"), "bicycle"),
    **dict.fromkeys(("motorbike", "scooter", "오토바이"), "motorcycle"),
    **dict.fromkeys(("van", "minivan", "suv", "taxi", "vehicle", "자동차", "차"), "car"),
    **dict.fromkeys(("plane", "jet", "비행기"), "airplane"),
    **dict.fromkeys(("ship", "배"), "boat"),
    **dict.fromkeys(("train car", "railcar", "subway", "기차"), "train"),
    **dict.fromkeys(("phone", "mobile phone", "smartphone", "cellphone", "휴대폰", "핸드폰", "폰"), "cell phone"),
    **dict.fromkeys(("mug", "coffee cup", "머그컵", "컵"), "cup"),
    **dict.fromkeys(("bag", "purse", "가방"), "handbag"),
    **dict.fromkeys(("luggage", "캐리어"), "suitcase"),
    **dict.fromkeys(("teddy", "stuffed animal", "plush", "doll", "곰인형", "인형"), "teddy bear"),
    **dict.fromkeys(("flower pot", "plant pot", "pot plant", "plant", "houseplant", "화분"), "potted plant"),
    **dict.fromkeys(("flower vase", "꽃병"), "vase"),
    **dict.fromkeys(("television", "monitor", "tv monitor"), "tv"),
    **dict.fromkeys(("sofa", "소파"), "couch"),
    **dict.fromkeys(("table", "desk", "식탁"), "dining table"),
    **dict.fromkeys(("pizza piece", "pizza slice", "slice of pizza", "피자"), "pizza"),
    **dict.fromkeys(("doughnut",), "donut"),
    **dict.fromkeys(("remote control",), "remote"),
    **dict.fromkeys(("laptop computer", "notebook", "노트북"), "laptop"),
    **dict.fromkeys(("bird", "새"), "bird"),
    **dict.fromkeys(("horse", "말"), "horse"),
    **dict.fromkeys(("bus", "버스"), "bus"),
    **dict.fromkeys(("truck", "트럭"), "truck"),
    **dict.fromkeys(("chair", "의자"), "chair"),
    **dict.fromkeys(("bottle", "병"), "bottle"),
    **dict.fromkeys(("umbrella", "우산"), "umbrella"),
    **dict.fromkeys(("backpack", "백팩"), "backpack"),
}

# 규격 밖 effect → 규격 값 (모르는 값은 여전히 LLMError → 휴리스틱)
EFFECT_ALIASES: dict[str, str] = {
    **dict.fromkeys(("keep", "keep_only", "keep only", "retain", "isolate", "cutout", "cut_out",
                     "remove_background", "remove background", "background_removal", "transparent",
                     "transparent_background", "remove-bg", "removebg"), "remove_bg"),
    **dict.fromkeys(("erase", "delete", "remove", "inpaint", "remove_target", "object_removal",
                     "erase_object", "remove-object"), "remove_object"),
    **dict.fromkeys(("blur_background", "background_blur", "bokeh", "blur background"), "blur"),
    **dict.fromkeys(("cropping", "trim", "cut"), "crop"),
}


def canonical_target(name: str) -> str:
    """대상 이름 → COCO 클래스. 별칭 → 복수형 → 마지막 단어 순으로 맞춰 보고, 못 맞추면 그대로."""
    if name in COCO_CLASSES or name in STUFF_CLASSES:
        return name
    if name in TARGET_ALIASES:
        return TARGET_ALIASES[name]
    for cand in (name[:-2] if name.endswith("es") else None, name[:-1] if name.endswith("s") else None):
        if cand and (cand in COCO_CLASSES or cand in STUFF_CLASSES or cand in TARGET_ALIASES):
            return TARGET_ALIASES.get(cand, cand)
    words = name.split()
    if len(words) > 1:
        for size in range(len(words) - 1, 0, -1):  # "red sports car" → "sports car"? → "car"
            tail = " ".join(words[-size:])
            if tail in COCO_CLASSES or tail in STUFF_CLASSES or tail in TARGET_ALIASES:
                return TARGET_ALIASES.get(tail, tail)
    return name


def normalize_parsed(raw: Dict[str, Any]) -> ParsedPrompt:
    """LLM JSON → ParsedPrompt. 값 범위·어휘를 스키마에 맞게 보정한다.

    - target: 문자열/리스트 허용 → 소문자·공백 정리 → COCO 이름으로 (canonical_target) · 중복 제거, 비면 LLMError
    - effect: 별칭(keep → remove_bg 등) 정리 후에도 허용 목록 밖이면 LLMError (휴리스틱이 더 믿을 만함)
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
        name = canonical_target(_clean_phrase(t)) if t.strip() else ""
        if name and name not in targets:
            targets.append(name)
    if not targets:
        raise LLMError("target 비어 있음")

    effect = str(raw.get("effect") or "remove_bg").strip().lower()
    effect = EFFECT_ALIASES.get(effect, effect)
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

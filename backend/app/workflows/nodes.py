"""LangGraph 노드 함수.

오케스트레이션만 담당한다. 무거운 OpenCV/YOLO 연산은 services 로 위임.
노드 순서(요약):
  prompt_analyzer → preprocessor → segmentor → validator
  → (재시도|피드백) → effect_applier

이미지 ndarray 는 GraphState 에 넣지 않고 _IMAGE_CACHE[job_id] 에 둔다.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Dict
from uuid import uuid4

import cv2
from loguru import logger

from app.core.config import get_settings
from app.core.constants import JobStatus
from app.schemas.request import InstanceSelector, ParsedPrompt
from app.services.feedback_service import FeedbackService
from app.services.image_processor import ImageProcessor
from app.services.instance_selector import select_instances
from app.services import llm_models
from app.services.prompt_llm import clear_last_llm_provider, last_llm_provider, llm_chain, parse_prompt_llm
from app.services.prompt_rag import format_examples, get_prompt_rag
from app.services.segmentation import union_mask
from app.workflows.state import GraphState

# 모듈 수준 싱글톤 (첫 사용 시 생성 — lazy)
_processor: ImageProcessor | None = None
_feedback: FeedbackService | None = None
# job_id → {original, preprocessed, mask, result, ...}
# GraphState 에 ndarray 를 넣지 않기 위한 인메모리 캐시
_IMAGE_CACHE: Dict[str, Dict[str, Any]] = {}


_processor_lock = threading.Lock()


def _get_processor() -> ImageProcessor:
    """ImageProcessor 싱글톤 (세그멘터 포함).

    기동 시 미리 로드 스레드와 요청 스레드가 동시에 부를 수 있어 잠금으로 한 번만 만든다.
    """
    global _processor
    if _processor is None:
        with _processor_lock:
            if _processor is None:
                _processor = ImageProcessor()
    return _processor


def _get_feedback() -> FeedbackService:
    """FeedbackService 싱글톤."""
    global _feedback
    if _feedback is None:
        _feedback = FeedbackService()
    return _feedback


# 휴리스틱 키워드 표 — LLM 실패 시 fallback. 규격은 services/prompt_spec.SYSTEM_PROMPT 와 맞춘다.
_REMOVE_VERBS = ("지워", "지우", "삭제", "없애", "제거", "치워", "치우", "빼줘", "빼 줘", "remove", "erase", "delete", "wipe out")
_BLUR_WORDS = ("blur", "블러", "흐리", "흐릿", "뿌옇", "흐림", "bokeh", "out of focus")
_CROP_WORDS = ("crop", "크롭", "잘라", "오려", "trim")
# 이 표현이 있으면 "대상을 남기는" 요청 (배경 제거·제외하고 지우기)
_KEEP_HINTS = ("배경", "background", "제외", "빼고", "말고", "남기", "남겨", "만 남", "keep", "except", "only")
_POSITION_WORDS = [
    ("front", ("맨 앞", "제일 앞", "가장 앞", "앞에 있는", "앞쪽", "front", "closest")),
    ("back", ("맨 뒤", "제일 뒤", "가장 뒤", "뒤에 있는", "뒤쪽", "back", "farthest")),
    ("left", ("왼쪽", "좌측", "left")),
    ("right", ("오른쪽", "우측", "right")),
    ("center", ("가운데", "중앙", "center", "middle")),
    ("largest", ("가장 큰", "제일 큰", "biggest", "largest")),
    ("smallest", ("가장 작은", "제일 작은", "smallest")),
]
_COLOR_WORDS = [
    ("neon yellow", ("형광", "neon", "fluorescent")),
    ("red", ("빨간", "빨강", "붉은", "red")),
    ("orange", ("주황", "orange")),
    ("yellow", ("노란", "노랑", "yellow")),
    ("green", ("초록", "녹색", "green")),
    ("blue", ("파란", "파랑", "blue")),
    ("purple", ("보라", "purple")),
    ("pink", ("분홍", "핑크", "pink")),
    ("white", ("흰", "하얀", "white")),
    ("black", ("검은", "검정", "까만", "black")),
    ("gray", ("회색", "gray", "grey")),
    ("brown", ("갈색", "brown")),
]
_PART_WORDS = [
    ("helmet", ("안전모", "헬멧", "helmet")),
    ("hat", ("모자", "hat", "cap")),
    ("vest", ("조끼", "vest")),
    ("shirt", ("셔츠", "티셔츠", "상의", "shirt", "t-shirt")),
    ("jacket", ("자켓", "재킷", "점퍼", "jacket", "coat")),
    ("pants", ("바지", "하의", "pants", "jeans")),
    ("shoes", ("신발", "운동화", "shoes")),
]


def _heuristic_selector(text: str) -> InstanceSelector | None:
    """위치·개수·색 속성 키워드 → InstanceSelector (없으면 None)."""
    position = next(
        (pos for pos, keys in _POSITION_WORDS if any(k in text for k in keys)), None
    )

    rank = None
    ordinal = {"첫": 1, "두": 2, "세": 3, "네": 4, "다섯": 5}
    m_rank = re.search(r"(첫|두|세|네|다섯|\d)\s*(?:번째|째)", text)
    if m_rank:
        token = m_rank.group(1)
        rank = int(token) if token.isdigit() else ordinal[token]
    else:
        m_en = re.search(r"\b(second|third|fourth|fifth)\b", text)
        if m_en:
            rank = {"second": 2, "third": 3, "fourth": 4, "fifth": 5}[m_en.group(1)]
    if rank == 1:
        rank = None

    count = None
    m = re.search(r"(\d{1,2})\s*(?:명|마리|개|대)", text)
    if m:
        count = max(1, int(m.group(1)))
    elif re.search(r"한\s*(?:명|마리|개|대)|하나", text):
        count = 1

    # 색 단어 뒤 12자 이내 부위 단어가 있으면 "red helmet", 없으면 "red"
    attributes: list[str] = []
    for color, keys in _COLOR_WORDS:
        for k in keys:
            idx = text.find(k)
            if idx < 0:
                continue
            tail = text[idx + len(k) : idx + len(k) + 12]
            part = next(
                (name for name, pkeys in _PART_WORDS if any(pk in tail for pk in pkeys)), None
            )
            phrase = f"{color} {part}" if part else color
            if phrase not in attributes:
                attributes.append(phrase)
            break

    selector = InstanceSelector(position=position, rank=rank, count=count, attributes=attributes)
    return None if selector.is_empty() else selector


def parse_prompt_heuristic(prompt: str) -> ParsedPrompt:
    """
    LLM 없이 쓰는 Phase 1 휴리스틱 파서.
    예: '강아지만 남기고 배경 블러', 'person remove background'

    Ollama/OpenAI 연동 전에도 파이프라인이 돌아가게 하는 기본 구현.
    """
    # =============================================================================
    # [이미 구현된 구간 · 바이브] parse_prompt_heuristic 본문
    # -----------------------------------------------------------------------------
    # 스캐폴드/에이전트가 채운 Phase1 휴리스틱. 하드코딩 숙제 아님.
    # (키워드·효과 동의어 확장만 필요하면 여기 수정 — LLM 자리는 prompt_analyzer)
    # =============================================================================
    text = prompt.lower().strip()
    effect = "remove_bg"
    crop = False
    intensity = 15

    if any(w in text for w in _BLUR_WORDS):
        effect = "blur"
    if any(w in text for w in _CROP_WORDS):
        effect = "crop"
        crop = True
    # "X 지워줘" = 대상 지우기. 단 "배경 제거"·"X 빼고 지워" 는 대상을 남기는 요청 (역할 분석으로 판정: heuristic_targets.analyze)
    from app.services.heuristic_targets import analyze

    detected, erase_intent = analyze(text)
    if erase_intent or (any(v in text for v in _REMOVE_VERBS) and not any(h in text for h in _KEEP_HINTS)):
        effect = "remove_object"

    m = re.search(r"(?:intensity|강도|blur)\s*[:=]?\s*(\d{1,3})", text)
    if m:
        intensity = max(0, min(100, int(m.group(1))))

    targets = []
    quoted = re.findall(r"[\"'“”](.+?)[\"'“”]", prompt)
    if quoted:
        targets = [q.strip() for q in quoted if q.strip()]
    else:
        # 어휘 확장 + 역할("X 말고 Y만") 규칙 — LLM 이 꺼졌을 때의 안전망 (services/heuristic_targets.py)
        targets = detected
    if not targets:
        targets = ["person"]

    return ParsedPrompt(
        target=targets,
        effect=effect,
        intensity=intensity,
        crop=crop,
        selector=_heuristic_selector(text),
    )


def prompt_analyzer(state: GraphState) -> GraphState:
    """노드: 자연어 → 구조화 ParsedPrompt (휴리스틱 / 이후 LLM·Ollama)."""
    prompt = state.get("prompt") or ""
    job_id = state.get("job_id") or uuid4().hex

    # 배치처럼 같은 문장을 여러 장에 쓸 때는 한 번만 해석해 넘긴다 (장마다 LLM 을 부르지 않게)
    if state.get("parsed_prompt"):
        return {
            **state,
            "job_id": job_id,
            "prompt_parser": "preset",
            "prompt_rag": [],
            "status": JobStatus.PENDING.value,
            "retry_count": state.get("retry_count") or 0,
        }

    # =============================================================================
    # [이미 구현된 구간 · 바이브] LLM 프롬프트 분석 연결
    # -----------------------------------------------------------------------------
    # Settings.llm_provider 에 따라 services/prompt_llm 이 Ollama/OpenAI/Gemini 호출.
    #   - heuristic/빈 값/미지원 provider → None → 휴리스틱
    #   - 호출·파싱 실패(LLMError 등)      → 경고 로그 후 휴리스틱
    # prompt_parser 에 실제 사용된 파서를 남겨 meta/콘솔에서 확인 가능.
    # =============================================================================
    parsed: ParsedPrompt | None = None
    parser_used = "heuristic"
    # 작업실에서 고른 해석 모델은 이 요청에만 적용한다 (설정 복사본 — 서버 설정은 그대로)
    settings = llm_models.with_model(get_settings(), state.get("llm_model"))
    rag_hits: list = []
    examples = ""
    provider = (settings.llm_provider or "").strip().lower()
    chain = llm_chain(settings)
    if settings.prompt_rag_enabled and any(p in {"ollama", "openai", "gemini"} for p in chain):
        # RAG: 비슷한 정답 예시(사용자 교정·좋아요·시드)를 찾아 LLM 지시문에 붙인다
        try:
            rag_hits = get_prompt_rag(settings).retrieve(prompt)
            examples = format_examples(rag_hits)
        except Exception as exc:  # 검색 실패는 예시 없이 진행
            logger.warning("프롬프트 RAG 검색 실패 job={}: {}", job_id, exc)
    clear_last_llm_provider()
    try:
        if settings.prompt_chain == "langchain" and settings.prompt_votes > 1:
            # 키워드 파서와 대상이 다르면 여러 번 물어 다수결 (services/prompt_chain.py, LangChain Core)
            from app.services.prompt_chain import parse_prompt_chain

            parsed = parse_prompt_chain(
                prompt, settings, examples=examples,
                ask=lambda p, s, e="": parse_prompt_llm(p, s, examples=e),  # 이 모듈의 이름을 거쳐야 테스트의 가짜가 적용된다
            )
        else:
            parsed = parse_prompt_llm(prompt, settings, examples=examples)
        if parsed is not None:
            # fallback 이 성공하면 기본 provider 가 아니라 실제 성공한 이름을 남긴다.
            # parse_prompt_llm 이 테스트에서 교체되면 기록이 비어 기본 이름을 쓴다.
            parser_used = last_llm_provider() or provider
    except Exception as exc:
        logger.warning("LLM 프롬프트 분석 실패 job={} — 휴리스틱 사용: {}", job_id, exc)
        parsed = None

    # =============================================================================
    # [이미 구현된 구간 · 바이브] heuristic fallback + state 반환
    # -----------------------------------------------------------------------------
    # LLM 미연결·실패 시에도 파이프라인이 돌아가게 하는 기존 동작.
    # =============================================================================
    if parsed is None:
        parsed = parse_prompt_heuristic(prompt)
    logger.info(
        "prompt_analyzer job={} parser={} parsed={}",
        job_id,
        parser_used,
        parsed.model_dump(),
    )
    return {
        **state,
        "job_id": job_id,
        "parsed_prompt": parsed.model_dump(),
        "prompt_parser": parser_used,
        "llm_model": settings.ollama_model if parser_used == "ollama" else None,  # 실제로 Ollama 가 해석했을 때만 어느 모델이었는지 남긴다
        # 다른 사용자의 문장은 남기지 않고 출처·점수만 (교정 예시는 모든 사용자 해석에 쓰임)
        "prompt_rag": [{"source": h.example.source, "score": h.score} for h in rag_hits],
        "status": JobStatus.PENDING.value,
        "retry_count": state.get("retry_count") or 0,
    }


def preprocessor(state: GraphState) -> GraphState:
    """노드: 디코드 + CLAHE 전처리 (ImageProcessor).

    결과 이미지는 GraphState 가 아니라 _IMAGE_CACHE 에 보관한다.
    """
    job_id = state["job_id"]
    image_bytes = state.get("image_bytes")
    if not image_bytes:
        return {**state, "status": JobStatus.FAILED.value, "error": "image_bytes 없음"}

    processor = _get_processor()
    from app.utils.image_utils import decode_image_bytes

    from app.utils.image_utils import resize_keep_aspect

    original = decode_image_bytes(image_bytes)
    preprocessed = processor.preprocess(original)
    # CLAHE 없이 크기만 맞춘 사본 — 재시도에서 대비 보정이 오히려 해가 된 경우를 위해
    resized, _ = resize_keep_aspect(original, processor.settings.max_image_side)
    # 이후 노드(segmentor, effect)가 참조할 캐시
    _IMAGE_CACHE[job_id] = {
        "original": original,
        "preprocessed": preprocessed,
        "resized": resized,
        "image_bytes": image_bytes,
        "attempts": [],
    }
    return {**state, "message": "preprocessed"}


# 【수동·튜닝】 재시도 전략 — 같은 입력으로 다시 돌리면 결과가 같으므로 조건을 바꾼다
#   1차: 설정(PREPROCESS_CLAHE, 기본 꺼짐)대로의 입력 + 기본 신뢰도 기준
#   2차: 반대쪽 전처리 입력 + 신뢰도 기준 × RETRY_CONFIDENCE_SCALE
RETRY_CONFIDENCE_SCALE = 0.6


def segmentor(state: GraphState) -> GraphState:
    """노드: 세그멘테이션 실행. 재시도면 입력 이미지와 신뢰도 기준을 바꿔서 다시 찾는다."""
    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    retry = int(state.get("retry_count") or 0) > 0
    processor = _get_processor()
    # 기본 입력은 설정 따라 (CLAHE 끔 = 크기만 맞춘 사본), 재시도는 반대쪽 — 한쪽이 못 찾은 것을 다른 쪽이 찾는 경우를 노린다
    use_clahe = processor.settings.preprocess_clahe != retry
    pre = cache.get("preprocessed" if use_clahe else "resized")
    if pre is None:
        pre = cache.get("resized") if cache.get("resized") is not None else cache.get("preprocessed")
    if pre is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "전처리 이미지 없음"}

    # state 의 dict 를 다시 ParsedPrompt 로
    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    min_conf = processor.settings.min_confidence * RETRY_CONFIDENCE_SCALE if retry else None
    strategy = "retry_alt_preprocess_lowconf" if retry else "default"
    seg = processor.segmentor.predict(pre, targets=parsed.target, min_confidence=min_conf)
    if retry:
        logger.info("segmentor 재시도 job={} strategy={} min_conf={}", job_id, strategy, min_conf)

    # selector 가 있으면 같은 클래스 인스턴스 중 일부만 고른다 (위치·개수·색)
    mask, labels, confidences = seg.mask, seg.labels, seg.confidences
    selection = None
    chosen = list(seg.instances)
    if parsed.selector is not None and seg.instances:
        picked = select_instances(seg.instances, parsed.selector, pre)
        chosen = list(picked.chosen)
        mask = union_mask(picked.chosen, pre.shape[:2])
        labels = [i.label for i in picked.chosen]
        confidences = [i.confidence for i in picked.chosen]
        selection = {
            "chosen": len(picked.chosen),
            "candidates": len(seg.instances),
            "attribute_matched": picked.attribute_matched,
            "attribute_scores": [
                None if s is None else round(s, 3) for s in picked.attribute_scores
            ],
            "note": picked.note,
        }
        logger.info("instance_selector job={} {}", job_id, selection)

    # 지정하지 않은 사람·동물·물체가 대상에 붙어 남지 않게: 다른 인스턴스 몫을 덜어내고(MASK_EXCLUSIVE),
    # 경계 정제가 되가져오지 못하게 구역을 기록(MASK_FORBID_REFINE)
    cache["forbid"] = None
    leak = None
    if chosen:
        from app.services.mask_exclusion import finalize_selection, leak_signals

        before = mask
        mask, cache["forbid"] = finalize_selection(seg, chosen, pre.shape[:2], processor.settings)
        leak = leak_signals(seg, chosen, before, mask)

    # 마스크·세그 메타를 캐시에 저장
    cache["mask"] = mask
    cache["seg"] = seg
    _IMAGE_CACHE[job_id] = cache
    return {
        **state,
        "confidences": confidences,
        "labels": labels,
        "detected": seg.detected,
        "selection": selection,
        "leak": leak,
        "backend": seg.backend,
        "segment_strategy": strategy,
        "message": "segmented",
    }


def validator_node(state: GraphState) -> GraphState:
    """노드: 마스크 품질 점수 계산 → status ok/fallback/failed."""
    from app.services.validator import score_mask

    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    mask = cache.get("mask")
    if mask is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "마스크 없음"}

    confidences = state.get("confidences") or []
    result = score_mask(mask, confidences)
    message = result.message
    if not mask.any():
        # 빈 마스크 = 요청 대상을 못 찾음 → 사용자가 이해할 수 있는 안내로 교체
        targets = (state.get("parsed_prompt") or {}).get("target") or []
        detected = sorted(set(state.get("detected") or []))
        message = f"요청한 대상({', '.join(targets)})을 이미지에서 찾지 못했습니다."
        if detected:
            message += f" 감지된 대상: {', '.join(detected)}"
    scored = {
        **state,
        "status": result.status,
        "quality_score": result.quality_score,
        "message": message,
        "error": None if result.ok else message,
    }
    return _keep_best_attempt(scored, cache, mask)


_STATUS_RANK = {JobStatus.OK.value: 2, JobStatus.FALLBACK.value: 1, JobStatus.FAILED.value: 0}
_ATTEMPT_KEYS = ("status", "quality_score", "message", "error", "labels", "confidences",
                 "detected", "selection", "segment_strategy", "leak")


def _keep_best_attempt(scored: GraphState, cache: Dict[str, Any], mask: Any) -> GraphState:
    """시도마다 결과를 기록하고, 재시도 뒤에는 (상태, 품질 점수)가 더 나은 시도를 채택한다.

    완화한 조건이 오히려 엉뚱한 마스크를 만들 수 있으므로 무조건 마지막 시도를 쓰지 않는다.
    """
    attempts = cache.setdefault("attempts", [])
    attempts.append({"mask": mask, **{k: scored.get(k) for k in _ATTEMPT_KEYS}})
    if len(attempts) < 2:
        return {**scored, "attempts": len(attempts)}
    # 인덱스로 고른다 (dict 안의 numpy 마스크끼리 == 비교를 피하기 위해 list.index 를 쓰지 않음)
    best_i = max(
        range(len(attempts)),
        key=lambda i: (
            _STATUS_RANK.get(attempts[i]["status"] or "", 0),
            float(attempts[i]["quality_score"] or 0.0),
        ),
    )
    best = attempts[best_i]
    cache["mask"] = best["mask"]
    chosen = best_i + 1
    if chosen != len(attempts):
        logger.info("재시도 결과가 더 나빠 {}번째 시도를 채택", chosen)
    return {
        **scored,
        **{k: best[k] for k in _ATTEMPT_KEYS},
        "attempts": len(attempts),
        "chosen_attempt": chosen,
    }


def effect_applier(state: GraphState) -> GraphState:
    """노드: 마스크 정제 + 블러/크롭/배경제거 적용 후 디스크 저장."""
    from app.services.effects import apply_effects, refine_mask, upscale_mask
    from app.core.config import get_settings
    from app.utils.image_utils import ensure_dir, save_image

    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    original = cache.get("original")
    mask = cache.get("mask")
    if original is None or mask is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "이미지/마스크 없음"}

    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    if mask.shape[:2] != original.shape[:2]:
        # 세그는 리사이즈된 전처리 이미지 기준 → 원본 크기로 맞춤 (큰 사진 크기 불일치 방지)
        # 선형 보간 + 절반 임계 — 최근접 보간은 확대 배율만큼 계단이 생긴다
        oh, ow = original.shape[:2]
        mask = upscale_mask(mask, (ow, oh))
    if mask.any():
        # remove_object 는 윤곽까지 지워야 해서 GrabCut 정제 없이 원 마스크 사용.
        # 정제는 여기서 한 번만 — apply_effects 가 또 하면 경계가 깎인다(refine=False)
        forbid = cache.get("forbid")
        if forbid is not None and forbid.shape[:2] != original.shape[:2]:
            forbid = upscale_mask(forbid, (original.shape[1], original.shape[0]))
        refined = mask if parsed.effect == "remove_object" else refine_mask(mask, original, forbid)  # GrabCut 은 MASK_GRABCUT
        result_img = apply_effects(original, refined, parsed, refine=False)
    else:
        # 대상 없음: 전부 투명/전부 블러 대신 원본 유지 (status 는 failed 그대로)
        result_img = original.copy()
    cache["result"] = result_img
    _IMAGE_CACHE[job_id] = cache

    # data/uploads/{job_id}/before|after 저장
    settings = get_settings()
    out_dir = settings.upload_path / job_id
    ensure_dir(out_dir)
    before_path = out_dir / "before.jpg"
    # 알파 채널 있으면 PNG, 아니면 JPG
    after_img = result_img
    if after_img.ndim == 3 and after_img.shape[2] == 4:
        after_path = out_dir / "after.png"
    else:
        after_path = out_dir / "after.jpg"
    save_image(before_path, original)
    save_image(after_path, after_img)

    # pending 이면 성공 처리로 승격
    status = state.get("status") or JobStatus.OK.value
    if status == JobStatus.PENDING.value:
        status = JobStatus.OK.value

    return {
        **state,
        "before_path": str(before_path),
        "after_path": str(after_path),
        "status": status,
        "message": state.get("message") or "effects_applied",
    }


def feedback_collector(state: GraphState) -> GraphState:
    """노드: 실패/fallback 케이스 영속화 (DB + 파일 사이드카).

    비로그인 요청(persist=False)은 이미지를 남기지 않는다 — 저장 없이 다운로드만 제공.
    """
    if state.get("persist") is False:
        return {**state, "feedback_saved": False}
    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    original = cache.get("original")
    # 실패 메타와 함께 저장 → 이후 학습 데이터로 활용 가능
    row, path = _get_feedback().save_failure(
        job_id=job_id,
        image=original,
        meta={
            "prompt": state.get("prompt"),
            "parsed_prompt": state.get("parsed_prompt"),
            "quality_score": state.get("quality_score"),
            "error": state.get("error"),
            "backend": state.get("backend"),
            "labels": state.get("labels"),
            "detected": state.get("detected"),
            "selection": state.get("selection"),
            "leak": state.get("leak"),
            # 처리는 성공했지만 확신이 낮아 모은 사례 — 검수·재학습 때 실패 사례와 구분한다
            "hard_example": state.get("status") == JobStatus.OK.value,
        },
    )
    return {
        **state,
        "feedback_saved": True,
        "feedback_meta": {
            "path": str(path) if path else None,
            "feedback_id": row.id if row else None,
        },
        "message": "feedback_saved",
    }


def clear_job_cache(job_id: str) -> None:
    """요청 종료 시 인메모리 이미지 캐시 제거 (메모리 누수 방지)."""
    _IMAGE_CACHE.pop(job_id, None)

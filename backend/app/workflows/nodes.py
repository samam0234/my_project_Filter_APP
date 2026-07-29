"""LangGraph 노드 함수.

오케스트레이션만 담당한다. 무거운 OpenCV/YOLO 연산은 services 로 위임.
노드 순서(요약):
  prompt_analyzer → preprocessor → segmentor → validator
  → (재시도|피드백) → effect_applier

이미지 ndarray 는 GraphState 에 넣지 않고 _IMAGE_CACHE[job_id] 에 둔다.
"""

from __future__ import annotations

import re
from typing import Any, Dict
from uuid import uuid4

from loguru import logger

from app.core.constants import JobStatus
from app.schemas.request import ParsedPrompt
from app.services.feedback_service import FeedbackService
from app.services.image_processor import ImageProcessor
from app.workflows.state import GraphState

# 모듈 수준 싱글톤 (첫 사용 시 생성 — lazy)
_processor: ImageProcessor | None = None
_feedback: FeedbackService | None = None
# job_id → {original, preprocessed, mask, result, ...}
# GraphState 에 ndarray 를 넣지 않기 위한 인메모리 캐시
_IMAGE_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_processor() -> ImageProcessor:
    """ImageProcessor 싱글톤 (세그멘터 포함)."""
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor


def _get_feedback() -> FeedbackService:
    """FeedbackService 싱글톤."""
    global _feedback
    if _feedback is None:
        _feedback = FeedbackService()
    return _feedback


def parse_prompt_heuristic(prompt: str) -> ParsedPrompt:
    """
    LLM 없이 쓰는 Phase 1 휴리스틱 파서.
    예: '강아지만 남기고 배경 블러', 'person remove background'

    Ollama/OpenAI 연동 전에도 파이프라인이 돌아가게 하는 기본 구현.
    """
    text = prompt.lower().strip()
    # 【수동】 기본 effect / intensity
    # 조건: 프롬프트에 효과 키워드가 없을 때 적용
    # 기능: ParsedPrompt.effect → effects.apply_effects 분기 (remove_bg|blur|crop|none)
    effect = "remove_bg"
    crop = False
    intensity = 15

    # 효과 키워드 (한/영)
    # 【수동·하드코딩】 지원 효과 동의어 사전
    # 조건: 사용자 자연어에 아래 문자열이 포함되면 해당 effect 로 덮어씀
    # 기능: 새 효과(예: mosaic) 추가 시 여기 + EffectType + apply_effects 동시 수정
    if "blur" in text or "블러" in text:
        effect = "blur"
    if "crop" in text or "크롭" in text or "잘라" in text:
        effect = "crop"
        crop = True
    if "크롭" in text or "crop" in text:
        crop = True

    # 강도 예: "blur 20" / "강도 20"
    m = re.search(r"(?:intensity|강도|blur)\s*[:=]?\s*(\d{1,3})", text)
    if m:
        intensity = max(0, min(100, int(m.group(1))))

    # 대상 추출: 따옴표 안 문구 우선, 없으면 클래스 키워드 매칭
    targets = []
    quoted = re.findall(r"[\"'“”](.+?)[\"'“”]", prompt)
    if quoted:
        targets = [q.strip() for q in quoted if q.strip()]
    else:
        # 【수동·하드코딩·중요】 한국어/영어 키워드 → YOLO 클래스 이름 매핑
        # 조건:
        #   1) 오른쪽 리스트(keys) 중 하나가 프롬프트에 포함되면 left label 추가
        #   2) label 문자열은 YOLO 모델 names 와 소문자로 일치해야 마스크 필터가 먹음
        #      (학습 시 training/configs 의 names 와 동일하게 유지)
        # 기능: 지원 대상 클래스 확장 (예: "bottle", "컵") 시 행 추가
        # 한계: LLM 미연동 시 여기 사전에 없는 말은 인식 못 함 → person 기본
        keywords = [
            ("person", ["person", "사람", "인물"]),
            ("dog", ["dog", "강아지", "개"]),
            ("cat", ["cat", "고양이"]),
            ("car", ["car", "차", "자동차"]),
            ("bag", ["bag", "가방"]),
        ]
        for label, keys in keywords:
            if any(k in text for k in keys):
                targets.append(label)
    # 【수동】 기본 target — 매칭 실패 시 세그가 이 클래스만 남기려 시도
    if not targets:
        targets = ["person"]

    return ParsedPrompt(target=targets, effect=effect, intensity=intensity, crop=crop)


def prompt_analyzer(state: GraphState) -> GraphState:
    """노드: 자연어 → 구조화 ParsedPrompt (휴리스틱 / 이후 LLM·Ollama)."""
    prompt = state.get("prompt") or ""
    # job_id 없으면 새로 발급
    job_id = state.get("job_id") or uuid4().hex

    # ---
    # 제목 (하드코딩 파트 부분 : [LLM 프롬프트 분석 연결])
    # [관련 작업 임무 및 역할]
    #   Settings 의 LLM_* 설정을 읽어 자연어 prompt → ParsedPrompt JSON 으로 변환한다.
    #   Phase1 완성도 부족분(~30% 중 핵심): 휴리스틱만 쓰는 한계를 LLM 으로 메운다.
    # [기능하고 연결된 변수 및 함수]
    #   - 입력: prompt (str), state
    #   - 설정: get_settings().llm_provider / llm_base_url / ollama_model /
    #           openai_api_key / openai_model / gemini_api_key / gemini_model
    #   - 스키마: app.schemas.request.ParsedPrompt (target, effect, intensity, crop)
    #   - 실패 시: parse_prompt_heuristic(prompt) 로 fallback (아래 한 줄 유지 가능)
    #   - 출력: parsed → state["parsed_prompt"]
    # [작성해야 하는 방식 및 규칙]
    #   1) llm_provider 가 heuristic 이거나 빈 값이면 LLM 호출 생략 → 휴리스틱만.
    #   2) ollama | openai | gemini 일 때만 HTTP/SDK 호출.
    #   3) 모델 응답은 JSON 만: {"target":[...],"effect":"...","intensity":0~100,"crop":bool}
    #   4) effect 허용값: remove_bg | blur | crop | none (그 외면 heuristic 또는 remove_bg)
    #   5) target 라벨은 소문자, YOLO names / keywords 라벨과 맞출 것.
    #   6) 타임아웃·파싱 실패·네트워크 오류 시 예외 삼키고 heuristic fallback.
    #   7) 이 함수 안에서 OpenCV/YOLO 호출 금지 (오케스트레이션만).
    # [코드 방식 힌트]
    #   settings = get_settings()
    #   try:
    #       if settings.llm_provider == "ollama":
    #           # requests.post(f"{base}/api/chat", json={model, messages, format:"json"})
    #           # data = response.json() → content 파싱 → ParsedPrompt(**...)
    #       elif settings.llm_provider == "openai":
    #           ...
    #       else:
    #           parsed = parse_prompt_heuristic(prompt)
    #   except Exception:
    #       parsed = parse_prompt_heuristic(prompt)
    # ---
    # (위 규칙대로 LLM 분기 작성. 미구현 동안은 아래 heuristic 유지)
    parsed = parse_prompt_heuristic(prompt)
    logger.info("prompt_analyzer job={} parsed={}", job_id, parsed.model_dump())
    return {
        **state,
        "job_id": job_id,
        "parsed_prompt": parsed.model_dump(),
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

    original = decode_image_bytes(image_bytes)
    preprocessed = processor.preprocess(original)
    # 이후 노드(segmentor, effect)가 참조할 캐시
    _IMAGE_CACHE[job_id] = {
        "original": original,
        "preprocessed": preprocessed,
        "image_bytes": image_bytes,
    }
    return {**state, "message": "preprocessed"}


def segmentor(state: GraphState) -> GraphState:
    """노드: 전처리 이미지에 세그멘테이션 실행."""
    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    pre = cache.get("preprocessed")
    if pre is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "전처리 이미지 없음"}

    # state 의 dict 를 다시 ParsedPrompt 로
    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    processor = _get_processor()
    seg = processor.segmentor.predict(pre, targets=parsed.target)
    # 마스크·세그 메타를 캐시에 저장
    cache["mask"] = seg.mask
    cache["seg"] = seg
    _IMAGE_CACHE[job_id] = cache
    return {
        **state,
        "confidences": seg.confidences,
        "labels": seg.labels,
        "backend": seg.backend,
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
    return {
        **state,
        "status": result.status,
        "quality_score": result.quality_score,
        "message": result.message,
        "error": None if result.ok else result.message,
    }


def effect_applier(state: GraphState) -> GraphState:
    """노드: 마스크 정제 + 블러/크롭/배경제거 적용 후 디스크 저장."""
    from app.services.effects import apply_effects, refine_mask
    from app.core.config import get_settings
    from app.utils.image_utils import ensure_dir, save_image

    job_id = state["job_id"]
    cache = _IMAGE_CACHE.get(job_id) or {}
    original = cache.get("original")
    mask = cache.get("mask")
    if original is None or mask is None:
        return {**state, "status": JobStatus.FAILED.value, "error": "이미지/마스크 없음"}

    parsed = ParsedPrompt(**(state.get("parsed_prompt") or {}))
    refined = refine_mask(mask, original)
    result_img = apply_effects(original, refined, parsed)
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
    """노드: 실패/fallback 케이스 영속화 (DB + 파일 사이드카)."""
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

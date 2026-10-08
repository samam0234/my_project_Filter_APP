"""운영 콘솔 "시스템" 화면용 런타임 스냅샷.

모델을 새로 로드하지 않는다 — 이미 올라온 것만 보고한다 (콘솔을 여는 것만으로 GPU 를 쓰지 않게).
Redis 는 배치를 Celery 로 보낼 때만 짧게 ping 한다.
"""

from __future__ import annotations

import shutil
from typing import Optional

from app import __version__
from app.core import preflight
from app.core.config import Settings, get_settings
from app.services.retention import storage_usage
from app.services.video_processor import ffmpeg_exe


def _segmentation(settings: Settings) -> dict:
    from app.workflows import nodes

    processor = nodes._processor  # 싱글톤을 만들지 않고 들여다보기만
    seg = processor.segmentor if processor is not None else None
    if seg is None:
        runtime = "not_loaded"
    elif getattr(seg, "_yolo", None) is not None:
        runtime = "ultralytics"
    elif getattr(seg, "_session", None) is not None:
        runtime = "onnx"
    else:
        runtime = "stub"
    return {
        "runtime": runtime,
        "model_file": settings.yolo_model_file.name,
        "model_exists": settings.yolo_model_file.is_file(),
        "prefer_onnx": settings.seg_prefer_onnx,
        "min_confidence": settings.min_confidence,
    }


def _open_vocab(settings: Settings) -> dict:
    from app.services import segmentation

    loaded = sorted(key.split(":", 1)[0] for key in segmentation._OV_CACHE)
    return {
        "enabled": settings.open_vocab_enabled,
        "dino_model_id": settings.dino_model_id,
        "sam2_model_id": settings.sam2_model_id,
        "box_threshold": settings.open_vocab_box_threshold,
        "text_threshold": settings.open_vocab_text_threshold,
        "loaded": loaded,
    }


def _stuff(settings: Settings) -> dict:
    """배경 덩어리(건물·하늘…) 모델 — 파일 유무와 로드 여부 (새로 로드하지 않는다)."""
    from app.workflows import nodes

    processor = nodes._processor
    seg = processor.segmentor if processor is not None else None
    loaded = bool(seg is not None and seg._stuff is not None and seg._stuff.available)
    return {
        "enabled": settings.stuff_seg_enabled,
        "model_file": settings.stuff_model_file.name,
        "model_exists": settings.stuff_model_file.is_file(),
        "min_prob": settings.stuff_min_prob,
        "loaded": loaded,
    }


def _mask(settings: Settings) -> dict:
    """대상 마스크 처리 설정 — 지정하지 않은 인물·동물·물체가 섞이는 문제를 다루는 값들 (docs/vaildates/leak-diagnosis-*.md)."""
    return {
        "exclusive": settings.mask_exclusive,
        "grabcut": settings.mask_grabcut,
        "forbid_refine": settings.mask_forbid_refine,
        "clahe": settings.preprocess_clahe,
        "hard_example_conf": settings.hard_example_conf,
    }


def _llm(settings: Settings) -> dict:
    provider = (settings.llm_provider or "").lower()
    model = {
        "ollama": settings.ollama_model,
        "openai": settings.openai_model,
        "gemini": settings.gemini_model,
    }.get(provider, "")
    return {
        "provider": provider,
        "model": model,
        "fallback": settings.llm_fallback,
        "chain": settings.prompt_chain,
        "votes": settings.prompt_votes if settings.prompt_chain == "langchain" else 1,
        "lora_adapter": bool(settings.lora_base_model),
        "rag_enabled": settings.prompt_rag_enabled,
        "rag_sources": settings.prompt_rag_sources,
    }


def _redis_ok(url: str) -> Optional[bool]:
    try:
        import redis
    except ImportError:
        return None
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        return bool(client.ping())
    except Exception:
        return False


def _batch(settings: Settings) -> dict:
    return {
        "use_celery": settings.batch_use_celery,
        # 꺼져 있으면 Redis 를 쓰지 않으므로 확인하지 않는다
        "redis_ok": _redis_ok(settings.redis_url) if settings.batch_use_celery else None,
    }


def _disk(settings: Settings) -> Optional[dict]:
    try:
        usage = shutil.disk_usage(settings.upload_path if settings.upload_path.exists() else ".")
    except OSError:
        return None
    return {"total": usage.total, "used": usage.used, "free": usage.free}


def snapshot(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    issues = preflight.check(settings)
    return {
        "version": __version__,
        "app_env": settings.app_env,
        "production": preflight.is_production(settings),
        "segmentation": _segmentation(settings),
        "open_vocab": _open_vocab(settings),
        "stuff_seg": _stuff(settings),
        "mask": _mask(settings),
        "llm": _llm(settings),
        "batch": _batch(settings),
        "video": {
            "output_format": settings.video_output_format,
            "ffmpeg": ffmpeg_exe() is not None,  # 없으면 mp4 를 못 만들고 webm → avi 로 내려간다
            "max_seconds": settings.video_max_seconds,
            "max_frames": settings.video_max_frames,
        },
        "console": {
            "require_login": settings.console_require_login,
            "admins": len(settings.console_admin_set),
            "allow_remote": settings.console_allow_remote,
        },
        "storage": {
            "retention_hours": settings.file_retention_hours,
            "areas": storage_usage(settings.upload_path, settings.file_retention_hours),
            "disk": _disk(settings),
        },
        "preflight": [{"level": i.level, "key": i.key, "message": i.message} for i in issues],
    }

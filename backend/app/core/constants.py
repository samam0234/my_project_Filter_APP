"""컷앤킵 공통 상수."""

from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    OK = "ok"
    FALLBACK = "fallback"
    FAILED = "failed"


class EffectType(str, Enum):
    REMOVE_BG = "remove_bg"
    BLUR = "blur"
    CROP = "crop"
    NONE = "none"


class FeedbackVote(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


# 허용 확장자 (MIME 검사와 함께 사용)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# API 접두사
API_V1_PREFIX = "/api/v1"

# Phase 표시 (문서 / 기능 플래그)
PHASE = 1
MAX_BATCH_SIZE = 500  # Phase 2

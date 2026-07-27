"""Shared constants for Cut & Keep."""

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


# Allowed file extensions (paired with MIME checks)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# API prefix
API_V1_PREFIX = "/api/v1"

# Phase markers (documentation / feature flags)
PHASE = 1
MAX_BATCH_SIZE = 500  # Phase 2

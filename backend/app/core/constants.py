"""컷앤킵 공통 상수.

문자열 매직 넘버 대신 Enum/상수로 공유한다.
JobStatus 값은 GraphState.status 및 DB jobs.status 와 동일해야 한다.
"""

from enum import Enum


class JobStatus(str, Enum):
    """처리 job 생명주기 상태."""

    PENDING = "pending"  # 접수·분석 중
    OK = "ok"  # 마스크 품질 통과
    FALLBACK = "fallback"  # 품질 미달 (재시도 또는 best-effort)
    FAILED = "failed"  # 복구 불가 실패


class EffectType(str, Enum):
    """적용 가능한 시각 효과 (ParsedPrompt.effect)."""

    REMOVE_BG = "remove_bg"
    BLUR = "blur"
    CROP = "crop"
    NONE = "none"


class FeedbackVote(str, Enum):
    """사용자/파이프라인 피드백 투표."""

    LIKE = "like"
    DISLIKE = "dislike"


# 허용 확장자 (MIME 검사와 함께 사용)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# API 접두사
API_V1_PREFIX = "/api/v1"

# Phase 표시 (문서 / 기능 플래그)
PHASE = 1
MAX_BATCH_SIZE = 500  # Phase 2 배치 업로드 상한

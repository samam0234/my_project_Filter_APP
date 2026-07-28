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


# -----------------------------------------------------------------------------
# 【수동】 허용 확장자 — security.validate_extension 과 동기
# 조건: 새 포맷(예: .heic) 추가 시 MIME 목록(config) + 프론트 dropzone accept 도 수정
# 기능: 업로드 파일 확장자 화이트리스트
# -----------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# API 접두사 — 라우터 prefix. 변경 시 프론트 api/client 경로도 전부 수정
API_V1_PREFIX = "/api/v1"

# 【수동】 Phase 표시 — /health 응답 phase 필드. 기능 게이트 문서용 숫자
PHASE = 1
# 【수동·Phase2】 배치 업로드 장수 상한 — routers/batch 에서 검사
MAX_BATCH_SIZE = 500

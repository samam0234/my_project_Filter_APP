"""LangGraph 노드 간 공유 GraphState.

노드 함수는 이 TypedDict 를 받아 일부 필드를 갱신한 새 dict 를 반환한다.
(불변 패턴에 가깝게 {**state, ...} 로 병합)

주의:
  - ndarray 등 직렬화 불가 객체는 여기 넣지 않는다.
    이미지는 nodes._IMAGE_CACHE[job_id] 에 보관한다.
  - total=False 이므로 모든 키가 필수는 아니다 (단계별로 채워짐).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict, total=False):
    # --- 식별 ---
    job_id: str  # 요청 단위 ID (업로드·파일 경로·DB PK 와 동일)

    # --- 입력 (API 에서 주입) ---
    image_bytes: bytes  # 원본 업로드 바이트 (전처리 전)
    image_path: Optional[str]  # 선택: 디스크 경로로 넘기는 경우
    prompt: str  # 사용자 자연어 프롬프트
    llm_model: Optional[str]  # 이 요청에서만 쓸 Ollama 해석 모델 (작업실 선택 상자) — 없으면 설정 기본

    # --- 프롬프트 분석 결과 ---
    # ParsedPrompt.model_dump() 형태: target, effect, intensity, crop
    parsed_prompt: Dict[str, Any]
    prompt_parser: str  # "ollama" | "openai" | "gemini" | "heuristic" (실제 사용된 파서)
    prompt_rag: List[Dict[str, Any]]  # RAG 로 붙인 예시의 출처·점수 (문장 원문은 남기지 않음)

    # --- 처리 상태 / 품질 ---
    # JSON 안전을 위해 TypedDict에 ndarray 미저장 — runner가 보관
    status: str  # pending | ok | fallback | failed
    error: Optional[str]  # 실패 메시지 (UI/로그용)
    quality_score: float  # 0.0~1.0 마스크 품질
    confidences: List[float]  # 인스턴스별 세그 confidence
    labels: List[str]  # 마스크에 포함된(요청 대상) 클래스 라벨
    detected: List[str]  # 필터 전 감지된 전체 라벨 (대상 못 찾음 안내용)
    selection: Optional[Dict[str, Any]]  # instance_selector 결과 요약 (chosen/candidates/속성 점수)
    leak: Optional[Dict[str, Any]]  # 대상에 다른 것이 섞였을 위험 신호 (mask_exclusion.leak_signals)
    backend: str  # "yolo" | "stub" 등

    # --- 산출물 경로 (디스크) ---
    before_path: Optional[str]  # data/uploads/{job_id}/before.jpg
    after_path: Optional[str]  # after.png 또는 after.jpg
    feedback_saved: bool  # 실패 케이스 영속화 여부
    feedback_meta: Dict[str, Any]  # 피드백 row/path 등

    # --- 제어 ---
    retry_count: int  # 세그 재시도 횟수 (현재 최대 1)
    persist: bool  # False = 비로그인 요청 → 피드백(학습 재료) 저장 안 함
    segment_strategy: str  # "default" | "retry_no_clahe_lowconf"
    attempts: int  # 세그·검증 시도 횟수
    chosen_attempt: int  # 재시도 뒤 채택된 시도 번호 (1-based)
    timings: Dict[str, float]  # 노드별 누적 소요 시간 (ms)
    message: str  # 단계별 짧은 상태 메시지

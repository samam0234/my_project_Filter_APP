/**
 * 사용자 앱 공유 타입 (백엔드 스키마와 맞춤).
 * 정본: backend/app/schemas/*.py, backend/app/services/prompt_spec.py
 */

/** 백엔드 JobStatus 와 동일 문자열 */
export type JobStatus = "pending" | "ok" | "fallback" | "failed";

export type Position = "front" | "back" | "left" | "right" | "center" | "largest" | "smallest";

export type Effect = "remove_bg" | "blur" | "crop" | "none" | "remove_object";

/** 특정 인스턴스 선택 조건 (ParsedPrompt.selector) */
export interface InstanceSelector {
  position?: Position | null;
  /** position 정렬에서 몇 번째부터 (1-based) */
  rank?: number | null;
  count?: number | null;
  attributes?: string[];
}

/** 프롬프트 분석 결과 (ParsedPrompt) */
export interface ParsedPrompt {
  target: string[];
  /** remove_bg | blur | crop | none (대상 남김) · remove_object (대상 지움) */
  effect: Effect | string;
  intensity: number;
  crop: boolean;
  selector?: InstanceSelector | null;
}

/** GET /health */
export interface HealthResponse {
  status: string;
  version: string;
  phase: number;
  db_dialect?: string | null;
}

/** POST /api/v1/upload 응답 */
export interface UploadResponse {
  job_id: string;
  status: JobStatus | string;
  parsed_prompt?: ParsedPrompt | null;
  before_url?: string | null;
  after_url?: string | null;
  quality_score: number;
  message?: string | null;
  feedback_saved: boolean;
}

/** GET /api/v1/jobs · /jobs/{id} */
export interface JobResponse {
  job_id: string;
  prompt: string;
  status: JobStatus | string;
  parsed_prompt?: ParsedPrompt | null;
  quality_score: number;
  before_url?: string | null;
  after_url?: string | null;
  backend?: string | null;
  message?: string | null;
  feedback_saved: boolean;
  /** UTC ISO 문자열 (시간대 표기 없음) */
  created_at?: string | null;
}

/** POST /api/v1/feedback 요청 */
export interface FeedbackRequest {
  job_id: string;
  vote: "like" | "dislike";
  /** dislike 일 때 ParsedPrompt JSON 이면 LoRA 학습 정답으로 쓰인다 */
  comment?: string;
}

/** POST /api/v1/feedback 응답 */
export interface FeedbackResponse {
  ok: boolean;
  job_id: string;
  feedback_id?: string | null;
  saved_path?: string | null;
  message: string;
}

/** POST /api/v1/batch · GET /api/v1/batch/{id} (Phase 2 스캐폴드) */
export interface BatchStatus {
  job_id: string;
  status: string;
  total?: number;
  completed?: number;
  progress?: number;
  message?: string | null;
}

/**
 * UI store 에 넣는 처리 결과 (camelCase).
 * API snake_case 를 훅에서 변환한다.
 */
export interface ProcessResultState {
  jobId: string;
  status: string;
  beforeUrl?: string | null;
  afterUrl?: string | null;
  qualityScore: number;
  parsedPrompt?: ParsedPrompt | null;
  message?: string | null;
}

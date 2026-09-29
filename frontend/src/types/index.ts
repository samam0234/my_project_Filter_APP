/**
 * 사용자 앱 공유 타입 (백엔드 스키마와 맞춤).
 */

/** 백엔드 JobStatus 와 동일 문자열 */
export type JobStatus = "pending" | "ok" | "fallback" | "failed";

/** 특정 인스턴스 선택 조건 (ParsedPrompt.selector) */
export interface InstanceSelector {
  position?: "front" | "back" | "left" | "right" | "center" | "largest" | "smallest" | null;
  /** position 정렬에서 몇 번째부터 (1-based) */
  rank?: number | null;
  count?: number | null;
  attributes?: string[];
}

/** 프롬프트 분석 결과 (ParsedPrompt) */
export interface ParsedPrompt {
  target: string[];
  /** remove_bg | blur | crop | none (대상 남김) · remove_object (대상 지움) */
  effect: string;
  intensity: number;
  crop: boolean;
  selector?: InstanceSelector | null;
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

/** POST /api/v1/feedback 요청 */
export interface FeedbackRequest {
  job_id: string;
  vote: "like" | "dislike";
  comment?: string;
}

/** POST /api/v1/feedback 응답 */
export interface FeedbackResponse {
  ok: boolean;
  job_id: string;
  saved_path?: string | null;
  message: string;
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

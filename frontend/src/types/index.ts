/**
 * 사용자 앱 공유 타입 (백엔드 스키마와 맞춤).
 */

/** 백엔드 JobStatus 와 동일 문자열 */
export type JobStatus = "pending" | "ok" | "fallback" | "failed";

/** 프롬프트 분석 결과 (ParsedPrompt) */
export interface ParsedPrompt {
  target: string[];
  effect: string;
  intensity: number;
  crop: boolean;
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

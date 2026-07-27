export type JobStatus = "pending" | "ok" | "fallback" | "failed";

export interface ParsedPrompt {
  target: string[];
  effect: string;
  intensity: number;
  crop: boolean;
}

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

export interface FeedbackRequest {
  job_id: string;
  vote: "like" | "dislike";
  comment?: string;
}

export interface FeedbackResponse {
  ok: boolean;
  job_id: string;
  saved_path?: string | null;
  message: string;
}

export interface ProcessResultState {
  jobId: string;
  status: string;
  beforeUrl?: string | null;
  afterUrl?: string | null;
  qualityScore: number;
  parsedPrompt?: ParsedPrompt | null;
  message?: string | null;
}

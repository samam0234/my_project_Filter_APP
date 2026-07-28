/**
 * 운영 콘솔 공유 타입 (백엔드 HealthResponse / JobResponse 와 맞춤).
 */

/** GET /health */
export interface HealthResponse {
  status: string;
  version: string;
  phase: number;
  db_dialect?: string | null;
}

/** GET /api/v1/jobs 항목 */
export interface JobResponse {
  job_id: string;
  prompt: string;
  status: string;
  parsed_prompt?: Record<string, unknown> | null;
  quality_score: number;
  before_url?: string | null;
  after_url?: string | null;
  backend?: string | null;
  message?: string | null;
  feedback_saved: boolean;
  created_at?: string | null;
}

/** 사이드바 페이지 키 */
export type ConsolePage = "dashboard" | "jobs" | "system" | "links";

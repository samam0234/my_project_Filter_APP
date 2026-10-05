/**
 * 운영 콘솔 공유 타입 (백엔드 HealthResponse / JobResponse 와 맞춤).
 */

/** GET /health */
export interface HealthResponse {
  status: string;
  version: string;
  phase: number;
  db_dialect?: string | null;
  /** 학습 DB 모드: mysql | sqlite | sqlite(fallback) */
  learning_db?: string | null;
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
export type ConsolePage = "dashboard" | "jobs" | "learning" | "system" | "links";

/** 학습 데이터 카탈로그 (학습 DB learning_samples) */
export type SampleStatus = "pending" | "approved" | "rejected";

export interface LearningSample {
  id: string;
  kind: "prompt" | "segment";
  source: "correction" | "like" | "request" | "pipeline_failure" | "pseudo_label" | string;
  status: SampleStatus;
  split?: "train" | "val" | null;
  origin_id: string;
  job_id?: string | null;
  user_id?: string | null;
  prompt?: string | null;
  answer?: Record<string, unknown> | null;
  has_image: boolean;
  image_url?: string | null;
  note?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface LearningSampleList {
  items: LearningSample[];
  total: number;
  limit: number;
  offset: number;
}

export interface LearningStats {
  by_status: Record<string, number>;
  by_source: Record<string, Record<string, number>>;
  approved_by_split: Record<string, number>;
  learning_db?: string | null;
}

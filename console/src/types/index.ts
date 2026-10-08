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

/** GET /api/v1/console/batches 항목 (전체 회원, 이미지 주소 없음) */
export interface BatchSummary {
  job_id: string;
  user_id?: string | null;
  status: string;
  progress?: number;
  total?: number;
  completed?: number;
  /** 완료된 장 중 처리하지 못한 수 */
  failed?: number;
  message?: string | null;
  prompt?: string | null;
  created_at?: string | null;
}

/** 사이드바 페이지 키 */
export type ConsolePage = "dashboard" | "jobs" | "batches" | "users" | "learning" | "system" | "links";

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
  /** 승인된 사용자 문장 수 (재학습 진행 표시) */
  approved_user_prompts?: number;
  /** 재학습 기준 (LORA_RETRAIN_MIN_NEW) */
  retrain_min_new?: number;
}

/** GET /api/v1/console/me — admin: CONSOLE_ADMINS 로그인 · local: 서버 PC(로그인 없음) · open: CONSOLE_ALLOW_REMOTE */
export interface ConsoleMe {
  via: "admin" | "local" | "open";
  username: string | null;
}

export type ConsoleAuthStatus = "checking" | "in" | "login";

/** GET /api/v1/console/users 항목 (비밀번호 해시 없음) */
export interface ConsoleUser {
  id: string;
  username: string;
  email: string;
  display_name: string | null;
  created_at: string | null;
  last_login_at: string | null;
  locked: boolean;
  locked_until: string | null;
  failed_logins: number;
  active_sessions: number;
  job_count: number;
  batch_count: number;
  /** CONSOLE_ADMINS 에 있는 계정 — 삭제 불가 */
  is_admin: boolean;
}

export interface ConsoleUserList {
  items: ConsoleUser[];
  total: number;
  limit: number;
  offset: number;
}

/** DELETE /api/v1/console/users/{id} 결과 */
export interface DeleteUserResult {
  id: string;
  username: string;
  jobs: number;
  batches: number;
  videos: number;
  removed_dirs: number;
  learning_unlinked: number;
}

/** GET /api/v1/console/system */
export interface StorageArea {
  name: "jobs" | "batches" | "videos";
  files: number;
  bytes: number;
  oldest_hours: number | null;
  /** 보관 기간이 지나 다음 정리에서 지워질 파일 */
  expired_files: number;
}

export interface SystemSnapshot {
  version: string;
  app_env: string;
  production: boolean;
  segmentation: { runtime: "not_loaded" | "ultralytics" | "onnx" | "stub"; model_file: string; model_exists: boolean; prefer_onnx: boolean; min_confidence: number };
  mask: { exclusive: string; grabcut: boolean; forbid_refine: boolean; clahe: boolean; hard_example_conf: number };
  stuff_seg: { enabled: boolean; model_file: string; model_exists: boolean; min_prob: number; loaded: boolean };
  open_vocab: { enabled: boolean; dino_model_id: string; sam2_model_id: string; box_threshold: number; text_threshold: number; loaded: string[] };
  llm: { provider: string; model: string; fallback: string; chain: string; votes: number; lora_adapter: boolean; rag_enabled: boolean; rag_sources: string };
  batch: { use_celery: boolean; redis_ok: boolean | null };
  video: { output_format: string; max_seconds: number; max_frames: number };
  console: { require_login: boolean; admins: number; allow_remote: boolean };
  storage: { retention_hours: number; areas: StorageArea[]; disk: { total: number; used: number; free: number } | null };
  preflight: { level: "error" | "warn"; key: string; message: string }[];
}

/** POST /api/v1/console/system/cleanup */
export interface CleanupResult {
  removed_files: number;
  freed_bytes: number;
  removed_dirs: number;
  dry_run: boolean;
  retention_hours: number;
}

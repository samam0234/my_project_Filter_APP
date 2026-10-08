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

/** 로그인 사용자 (GET /api/v1/auth/me) */
export interface AuthUser {
  id: string;
  username: string;
  email: string;
  display_name?: string | null;
  created_at?: string | null;
}

/** 계정 API 공통 안내 응답 */
export interface MessageResponse {
  ok: boolean;
  message: string;
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
  /** false = 비로그인 처리: 서버에 남기지 않음. after_url 은 data URL (다운로드만) */
  saved: boolean;
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
  /** image(사진) · video(영상) · gif — 예전 서버 응답에는 없을 수 있다 */
  kind?: JobKind;
  /** 작업 기록 썸네일 (영상은 첫 프레임 jpg, GIF 는 움직이는 결과) */
  thumb_url?: string | null;
  /** GIF 배경 제거: 반투명 경계를 살린 움직이는 WebP */
  webp_url?: string | null;
}

export type JobKind = "image" | "video" | "gif";

/** POST /api/v1/gif — 비로그인은 after_url 이 data URL(저장 안 함) */
export interface GifResponse {
  job_id: string;
  status: string;
  parsed_prompt?: ParsedPrompt | null;
  before_url?: string | null;
  after_url?: string | null;
  frames: number;
  total: number;
  held: number;
  effect: string;
  transparent: boolean;
  message?: string | null;
  saved: boolean;
  /** 배경 제거일 때만: 반투명 경계를 살린 움직이는 WebP (비로그인은 data URL) */
  webp_url?: string | null;
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

/** 배치 항목 하나 (GET /api/v1/batch/{id} 의 item_results[]) */
export interface BatchItem {
  index: number;
  filename: string;
  /** ok | fallback | failed — 실패 항목은 after_url 이 없다 */
  status: string;
  backend?: string | null;
  quality_score?: number;
  message?: string | null;
  output?: string | null;
  before_url: string;
  after_url?: string | null;
}

/** POST /api/v1/batch · GET /api/v1/batch/{id} */
export interface BatchStatus {
  job_id: string;
  /** queued | running | done | failed | not_found */
  status: string;
  total?: number;
  completed?: number;
  progress?: number;
  message?: string | null;
  prompt?: string;
  created_at?: string | null;
  item_results?: BatchItem[];
  /** 처리된 결과가 하나라도 있으면 zip 주소 */
  download_url?: string | null;
}

/** GET /api/v1/batch (내 배치 목록) 항목 */
export type BatchSummary = Pick<
  BatchStatus,
  "job_id" | "status" | "progress" | "total" | "completed" | "message" | "prompt" | "created_at"
>;

/** POST /api/v1/video 결과 — 비로그인은 파일만, 회원은 보관본 */
/** mp4 = H.264(기본) · webm = ffmpeg 가 없을 때 · avi = 둘 다 못 만들 때의 다운로드 전용(브라우저 재생 불가) */
export type VideoFormat = "mp4" | "webm" | "avi";

/** 서버가 해석한 효과와 요청 강도 — 화면에 보여 "무엇이 적용됐는지" 확인하게 한다 */
export interface VideoApplied {
  effect?: string;
  intensity?: number;
}

export type VideoResult =
  | ({ kind: "download"; blob: Blob; format: VideoFormat; frames: number; held: number } & VideoApplied)
  | ({ kind: "saved"; jobId: string; url: string; format: VideoFormat; frames: number; held: number } & VideoApplied);

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
  /** false = 비로그인 결과 (기록·피드백 없음, 다운로드만) */
  saved: boolean;
}

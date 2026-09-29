/**
 * 사용자 앱 ↔ FastAPI HTTP 클라이언트.
 *
 * VITE_API_BASE_URL 이 비어 있으면 동일 오리진(Vite 프록시) 기준.
 * 업로드 타임아웃 180s: LLM(Ollama) + YOLO 동기 처리, 첫 요청 모델 로드 여유.
 */
import axios from "axios";
import type {
  BatchStatus,
  FeedbackRequest,
  FeedbackResponse,
  HealthResponse,
  JobResponse,
  UploadResponse,
} from "../types";

// ---------------------------------------------------------------------------
// 【수동·.env】 VITE_API_BASE_URL
// 조건:
//   - 비움: Vite 프록시(/api,/health → 8000) 사용 (로컬 dev 권장)
//   - 설정: "http://localhost:8000" 등 절대 주소 (배포·콘솔 분리 시)
// 기능: axios baseURL
// ---------------------------------------------------------------------------
const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
});

/** 단일 이미지 업로드 + 프롬프트 처리 (파이프라인 동기 실행) */
export async function uploadImage(file: File, prompt: string): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  const { data } = await api.post<UploadResponse>("/api/v1/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180_000,
  });
  return data;
}

/** 최근 작업 목록 (최신순, 상한 200) */
export async function listJobs(limit = 50): Promise<JobResponse[]> {
  const { data } = await api.get<JobResponse[]>("/api/v1/jobs", { params: { limit } });
  return data;
}

/** 작업 단건 (없으면 404 → axios 에러) */
export async function getJob(jobId: string): Promise<JobResponse> {
  const { data } = await api.get<JobResponse>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);
  return data;
}

/** 결과 like/dislike (+ 정답 JSON 코멘트) */
export async function sendFeedback(body: FeedbackRequest): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/api/v1/feedback", body);
  return data;
}

/** 배치 등록 (Phase 2 스캐폴드 — 처리 없이 등록만) */
export async function createBatch(files: File[], prompt: string): Promise<BatchStatus> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("prompt", prompt);
  const { data } = await api.post<BatchStatus>("/api/v1/batch", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120_000,
  });
  return data;
}

/** 배치 상태 조회 */
export async function getBatch(jobId: string): Promise<BatchStatus> {
  const { data } = await api.get<BatchStatus>(`/api/v1/batch/${encodeURIComponent(jobId)}`);
  return data;
}

/** 헬스체크 */
export async function healthCheck(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health", { timeout: 5_000 });
  return data;
}

/**
 * 상대 API 자산 URL 을 baseURL(또는 현재 오리진 프록시)에 맞게 해석.
 * 예: /api/v1/files/xxx/before → http://localhost:8000/api/v1/...
 */
export function resolveAssetUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!baseURL) return url;
  return `${baseURL.replace(/\/$/, "")}${url}`;
}

/** axios 에러 → 사람이 읽을 메시지 (FastAPI detail 우선) */
export function errorMessage(err: unknown, fallback = "요청 중 오류가 발생했습니다."): string {
  const e = err as {
    response?: { status?: number; data?: { detail?: unknown } };
    code?: string;
    message?: string;
  };
  if (e?.code === "ECONNABORTED") return "시간이 초과되었습니다. 서버 상태를 확인하세요.";
  if (!e?.response && e?.message === "Network Error") {
    return "백엔드(:8000)에 연결할 수 없습니다.";
  }
  const detail = e?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "입력값을 확인하세요.";
  return e?.message || fallback;
}

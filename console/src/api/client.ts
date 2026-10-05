/**
 * 운영 콘솔 ↔ FastAPI HTTP 클라이언트.
 * 타임아웃 30s (목록 조회 위주, 업로드보다 짧게).
 */
import axios from "axios";
import type {
  HealthResponse,
  JobResponse,
  LearningSample,
  LearningSampleList,
  LearningStats,
} from "../types";

// ---------------------------------------------------------------------------
// 【수동·.env】 VITE_API_BASE_URL — frontend 와 동일 규칙
// 비움: vite proxy / 설정: http://localhost:8000 등
// ---------------------------------------------------------------------------
const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
});

/** GET /health */
export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

// 사용자 앱의 /api/v1/jobs 는 로그인 사용자 본인 작업만 돌려준다.
// 콘솔은 전체 작업을 보는 콘솔 전용 API 를 쓴다 — 서버 PC(loopback)에서만 허용 (CONSOLE_ALLOW_REMOTE).

/** GET /api/v1/console/jobs?limit= — 전체 작업 (소유자 무관) */
export async function fetchJobs(limit = 50): Promise<JobResponse[]> {
  const { data } = await api.get<JobResponse[]>("/api/v1/console/jobs", {
    params: { limit },
  });
  return data;
}

/** GET /api/v1/console/jobs/{id} */
export async function fetchJob(jobId: string): Promise<JobResponse> {
  const { data } = await api.get<JobResponse>(`/api/v1/console/jobs/${jobId}`);
  return data;
}

/** before/after 등 상대 URL 해석 */
export function resolveAssetUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!baseURL) return url;
  return `${baseURL.replace(/\/$/, "")}${url}`;
}

// ---------------------------------------------------------------------------
// 학습 데이터 검수 (학습 DB) — 승인된 문장 샘플만 RAG 예시 · LoRA 학습에 쓰인다
// ---------------------------------------------------------------------------

export interface SampleQuery {
  status?: string;
  source?: string;
  kind?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

/** GET /api/v1/console/learning/samples */
export async function fetchSamples(query: SampleQuery): Promise<LearningSampleList> {
  const params = Object.fromEntries(Object.entries(query).filter(([, v]) => v !== "" && v !== undefined));
  const { data } = await api.get<LearningSampleList>("/api/v1/console/learning/samples", { params });
  return data;
}

/** GET /api/v1/console/learning/stats */
export async function fetchLearningStats(): Promise<LearningStats> {
  const { data } = await api.get<LearningStats>("/api/v1/console/learning/stats");
  return data;
}

/** POST /api/v1/console/learning/samples/{id}/review — approve 시 answer 로 정답 수정 가능 */
export async function reviewSample(
  id: string,
  action: "approve" | "reject" | "reset",
  answer?: Record<string, unknown>,
  note?: string,
): Promise<LearningSample> {
  const { data } = await api.post<LearningSample>(`/api/v1/console/learning/samples/${id}/review`, {
    action,
    answer,
    note,
  });
  return data;
}

/** POST /api/v1/console/learning/samples/bulk */
export async function bulkReview(
  ids: string[],
  action: "approve" | "reject",
): Promise<{ done: number; skipped: { id: string; reason: string }[] }> {
  const { data } = await api.post("/api/v1/console/learning/samples/bulk", { ids, action });
  return data;
}

/** DELETE /api/v1/console/learning/samples/{id} — 원본 사이드카 파일까지 삭제 */
export async function deleteSample(id: string): Promise<{ id: string; removed_files: string[] }> {
  const { data } = await api.delete(`/api/v1/console/learning/samples/${id}`);
  return data;
}

/** axios 오류 → 사람이 읽을 메시지 */
export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    return err.message;
  }
  return String(err);
}

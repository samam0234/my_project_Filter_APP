/**
 * 운영 콘솔 ↔ FastAPI HTTP 클라이언트.
 * 타임아웃 30s (목록 조회 위주, 업로드보다 짧게).
 */
import axios from "axios";
import type { HealthResponse, JobResponse } from "../types";

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

/**
 * 운영 콘솔 ↔ FastAPI HTTP 클라이언트.
 * 타임아웃 30s (목록 조회 위주, 업로드보다 짧게).
 */
import axios from "axios";
import type { HealthResponse, JobResponse } from "../types";

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

/** GET /api/v1/jobs?limit= */
export async function fetchJobs(limit = 50): Promise<JobResponse[]> {
  const { data } = await api.get<JobResponse[]>("/api/v1/jobs", {
    params: { limit },
  });
  return data;
}

/** GET /api/v1/jobs/{id} */
export async function fetchJob(jobId: string): Promise<JobResponse> {
  const { data } = await api.get<JobResponse>(`/api/v1/jobs/${jobId}`);
  return data;
}

/** before/after 등 상대 URL 해석 */
export function resolveAssetUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!baseURL) return url;
  return `${baseURL.replace(/\/$/, "")}${url}`;
}

import axios from "axios";
import type { HealthResponse, JobResponse } from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
});

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function fetchJobs(limit = 50): Promise<JobResponse[]> {
  const { data } = await api.get<JobResponse[]>("/api/v1/jobs", {
    params: { limit },
  });
  return data;
}

export async function fetchJob(jobId: string): Promise<JobResponse> {
  const { data } = await api.get<JobResponse>(`/api/v1/jobs/${jobId}`);
  return data;
}

export function resolveAssetUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!baseURL) return url;
  return `${baseURL.replace(/\/$/, "")}${url}`;
}

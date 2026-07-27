import axios from "axios";
import type { FeedbackRequest, FeedbackResponse, UploadResponse } from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 120_000,
});

export async function uploadImage(
  file: File,
  prompt: string,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  const { data } = await api.post<UploadResponse>("/api/v1/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function sendFeedback(
  body: FeedbackRequest,
): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/api/v1/feedback", body);
  return data;
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get("/health");
  return data;
}

/** Resolve relative API asset URLs against baseURL (or current origin via proxy). */
export function resolveAssetUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (!baseURL) return url;
  return `${baseURL.replace(/\/$/, "")}${url}`;
}

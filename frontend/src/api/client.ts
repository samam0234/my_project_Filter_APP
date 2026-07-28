/**
 * 사용자 앱 ↔ FastAPI HTTP 클라이언트.
 *
 * VITE_API_BASE_URL 이 비어 있으면 동일 오리진(Vite 프록시) 기준.
 * 타임아웃 120s: YOLO 동기 처리 여유.
 */
import axios from "axios";
import type { FeedbackRequest, FeedbackResponse, UploadResponse } from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 120_000,
});

/** 단일 이미지 업로드 + 프롬프트 처리 */
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

/** 결과 like/dislike */
export async function sendFeedback(
  body: FeedbackRequest,
): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/api/v1/feedback", body);
  return data;
}

/** 헬스체크 (선택 사용) */
export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get("/health");
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

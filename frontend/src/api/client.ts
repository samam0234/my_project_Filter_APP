/**
 * 사용자 앱 ↔ FastAPI HTTP 클라이언트.
 *
 * VITE_API_BASE_URL 이 비어 있으면 동일 오리진(Vite 프록시) 기준.
 * 업로드 타임아웃 180s: LLM(Ollama) + YOLO 동기 처리, 첫 요청 모델 로드 여유.
 */
import axios from "axios";
import type {
  AuthUser,
  BatchStatus,
  BatchSummary,
  FeedbackRequest,
  FeedbackResponse,
  GifResponse,
  HealthResponse,
  JobResponse,
  MessageResponse,
  UploadResponse,
  VideoFormat,
  VideoResult,
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
  // 로그인 세션은 HttpOnly 쿠키 — 다른 오리진(baseURL 지정) 배포에서도 쿠키를 보내도록
  withCredentials: true,
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

/** 움직이는 GIF 한 개 처리 — 프레임마다 세그라 사진보다 오래 걸린다 */
export async function processGif(file: File, prompt: string): Promise<GifResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  const { data } = await api.post<GifResponse>("/api/v1/gif", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 600_000,
  });
  return data;
}

/** 로그인 사용자 본인 작업 목록 (최신순, 상한 200). 비로그인 401 */
export async function listJobs(limit = 50): Promise<JobResponse[]> {
  const { data } = await api.get<JobResponse[]>("/api/v1/jobs", { params: { limit } });
  return data;
}

// ---------------------------------------------------------------------------
// 계정 (/api/v1/auth) — 세션은 서버가 HttpOnly 쿠키로 관리
// ---------------------------------------------------------------------------

export async function fetchMe(): Promise<AuthUser | null> {
  try {
    const { data } = await api.get<AuthUser>("/api/v1/auth/me", { timeout: 8_000 });
    return data;
  } catch (err) {
    if ((err as { response?: { status?: number } })?.response?.status === 401) return null;
    throw err;
  }
}

export async function signupRequest(body: {
  username: string;
  email: string;
  password: string;
  display_name?: string;
  /** 만 14세 이상 · 이용약관 · 개인정보 처리방침 동의 — 서버가 true 가 아니면 가입하지 않는다 */
  agree_terms: boolean;
}): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>("/api/v1/auth/signup", body);
  return data;
}

export async function loginRequest(username: string, password: string): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>("/api/v1/auth/login", { username, password });
  return data;
}

export async function logoutRequest(): Promise<void> {
  await api.post("/api/v1/auth/logout");
}

export async function findIdRequest(email: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>("/api/v1/auth/find-id", { email });
  return data;
}

export async function passwordCodeRequest(username: string, email: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>("/api/v1/auth/password/request", {
    username,
    email,
  });
  return data;
}

export async function passwordResetRequest(
  username: string,
  code: string,
  newPassword: string,
): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>("/api/v1/auth/password/reset", {
    username,
    code,
    new_password: newPassword,
  });
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

/** 배치 등록 — 서버가 파일을 저장하고 한 장씩 처리한다 (진행률은 getBatch 폴링) */
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

/** 내 배치 목록 (최신순) */
export async function listBatches(limit = 30): Promise<BatchSummary[]> {
  const { data } = await api.get<BatchSummary[]>("/api/v1/batch", { params: { limit } });
  return data;
}

/**
 * 인증이 필요한 파일(zip·영상)을 받아 브라우저 다운로드로 저장.
 * <a href> 직접 링크는 다른 도메인 배포에서 쿠키가 안 가므로 axios(withCredentials)로 받는다.
 */
export async function downloadFile(url: string, filename: string): Promise<void> {
  saveBlob(await fetchBlob(url), filename);
}

/** 인증이 필요한 파일을 Blob 으로 (재생 미리보기·저장 공용) */
export async function fetchBlob(url: string): Promise<Blob> {
  try {
    const { data } = await api.get<Blob>(url, { responseType: "blob", timeout: 120_000 });
    return data;
  } catch (err) {
    throw await unwrapBlobError(err);
  }
}

/** Blob 을 문자열로 (Blob.text 가 없는 환경 — 일부 구형 브라우저·jsdom — 은 FileReader 로) */
function blobText(blob: Blob): Promise<string> {
  if (typeof blob.text === "function") return blob.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(blob);
  });
}

/** responseType: "blob" 요청의 오류 본문(JSON)은 Blob 으로 와서 errorMessage 가 못 읽는다 → 풀어서 다시 던진다 */
async function unwrapBlobError(err: unknown): Promise<unknown> {
  const e = err as { response?: { data?: unknown } };
  if (e?.response?.data instanceof Blob) {
    try {
      e.response.data = JSON.parse(await blobText(e.response.data));
    } catch {
      /* JSON 이 아니면 그대로 */
    }
  }
  return err;
}

/** Blob 을 파일로 저장 (비로그인 영상 결과 등) */
export function saveBlob(blob: Blob, filename: string): void {
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 10_000);
}

/**
 * 영상 한 개 처리. 동기 처리라 길게 기다린다 (프레임마다 세그).
 * 비로그인: avi 파일이 응답 본문(저장 없음) / 회원: JSON(보관본 job_id·url).
 */
/** 응답 헤더 · Content-Type 에서 영상 형식 판별 (헤더가 없는 프록시 대비) */
function videoFormat(header: string, contentType: string): VideoFormat {
  if (header === "mp4" || header === "webm" || header === "avi") return header;
  if (contentType.includes("mp4")) return "mp4";
  if (contentType.includes("webm")) return "webm";
  return "avi";
}

export async function processVideo(file: File, prompt: string): Promise<VideoResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("prompt", prompt);
  let res;
  try {
    res = await api.post<Blob>("/api/v1/video", form, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "blob",
      timeout: 600_000,
    });
  } catch (err) {
    throw await unwrapBlobError(err);
  }
  const contentType = String(res.headers["content-type"] ?? "");
  if (contentType.includes("json")) {
    const body = JSON.parse(await blobText(res.data)) as {
      job_id: string;
      url: string;
      format?: VideoFormat;
      effect?: string;
      intensity?: number;
      frames: number;
      held: number;
    };
    return {
      kind: "saved",
      jobId: body.job_id,
      url: body.url,
      format: body.format ?? "avi",
      effect: body.effect,
      intensity: body.intensity,
      frames: body.frames,
      held: body.held,
    };
  }
  return {
    kind: "download",
    blob: res.data,
    format: videoFormat(String(res.headers["x-cutnkeep-format"] ?? ""), contentType),
    effect: res.headers["x-cutnkeep-effect"] ? String(res.headers["x-cutnkeep-effect"]) : undefined,
    intensity: res.headers["x-cutnkeep-intensity"] ? Number(res.headers["x-cutnkeep-intensity"]) : undefined,
    frames: Number(res.headers["x-cutnkeep-frames"] ?? 0),
    held: Number(res.headers["x-cutnkeep-held"] ?? 0),
  };
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
  if (url.startsWith("http") || url.startsWith("data:") || url.startsWith("blob:")) return url;
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
  // 백엔드가 꺼져 있으면 Vite 프록시(개발)·nginx(배포)가 본문 없는 500/502/503/504 를 돌려준다
  const status = e?.response?.status ?? 0;
  if (status >= 500) {
    return "서버에 연결할 수 없거나 서버 오류가 발생했습니다. 백엔드(:8000)가 실행 중인지 확인해 주세요.";
  }
  return e?.message || fallback;
}

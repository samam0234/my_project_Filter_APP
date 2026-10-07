/**
 * 운영 콘솔 ↔ FastAPI HTTP 클라이언트.
 * 타임아웃 30s (목록 조회 위주, 업로드보다 짧게).
 */
import axios from "axios";
import type {
  BatchSummary,
  CleanupResult,
  ConsoleMe,
  ConsoleUserList,
  DeleteUserResult,
  HealthResponse,
  JobResponse,
  LearningSample,
  LearningSampleList,
  LearningStats,
  SystemSnapshot,
} from "../types";

// ---------------------------------------------------------------------------
// 【수동·.env】 VITE_API_BASE_URL — frontend 와 동일 규칙
// 비움: vite proxy / 설정: http://localhost:8000 등
// ---------------------------------------------------------------------------
const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
  // 관리자 세션 쿠키 — 콘솔과 API 가 다른 도메인이어도 보낸다
  withCredentials: true,
});

// 콘솔 API 가 401(로그인 필요) · 403(관리자 아님)을 주면 로그인 화면으로 — App 이 처리기를 등록한다
let onAuthRequired: ((message: string) => void) | null = null;
export function setAuthRequiredHandler(fn: ((message: string) => void) | null): void {
  onAuthRequired = fn;
}
api.interceptors.response.use(undefined, (err) => {
  const status = err?.response?.status;
  const url = String(err?.config?.url ?? "");
  if ((status === 401 || status === 403) && url.startsWith("/api/v1/console")) {
    onAuthRequired?.(errorMessage(err));
  }
  return Promise.reject(err);
});

/** GET /api/v1/console/me — 누구로 들어왔는지 (관리자 로그인 · 서버 PC) */
export async function fetchConsoleMe(): Promise<ConsoleMe> {
  const { data } = await api.get<ConsoleMe>("/api/v1/console/me");
  return data;
}

/** 사용자 앱과 같은 로그인 API — CONSOLE_ADMINS 에 있는 계정만 콘솔에 들어간다 */
export async function consoleLogin(username: string, password: string): Promise<void> {
  await api.post("/api/v1/auth/login", { username, password });
}

export async function consoleLogout(): Promise<void> {
  await api.post("/api/v1/auth/logout");
}

/** GET /health */
export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

// 사용자 앱의 /api/v1/jobs 는 로그인 사용자 본인 작업만 돌려준다.
// 콘솔은 전체 작업을 보는 콘솔 전용 API 를 쓴다 — 관리자 로그인(CONSOLE_ADMINS) 또는 서버 PC 에서만.

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

/** GET /api/v1/console/batches?limit= — 전체 회원 배치 현황 */
export async function fetchBatches(limit = 50): Promise<BatchSummary[]> {
  const { data } = await api.get<BatchSummary[]>("/api/v1/console/batches", { params: { limit } });
  return data;
}

// ---------------------------------------------------------------------------
// 회원 관리
// ---------------------------------------------------------------------------

/** GET /api/v1/console/users?q=&limit=&offset= */
export async function fetchUsers(q = "", limit = 50, offset = 0): Promise<ConsoleUserList> {
  const { data } = await api.get<ConsoleUserList>("/api/v1/console/users", { params: { q: q || undefined, limit, offset } });
  return data;
}

/** POST /api/v1/console/users/{id}/unlock — 로그인 실패 잠금 해제 */
export async function unlockUser(id: string): Promise<void> {
  await api.post(`/api/v1/console/users/${id}/unlock`);
}

/** POST /api/v1/console/users/{id}/sessions/revoke — 모든 기기에서 로그아웃 */
export async function revokeUserSessions(id: string): Promise<number> {
  const { data } = await api.post<{ revoked: number }>(`/api/v1/console/users/${id}/sessions/revoke`);
  return data.revoked;
}

/** DELETE /api/v1/console/users/{id} — confirm 에 아이디를 다시 입력해야 지워진다 (되돌릴 수 없음) */
export async function deleteUser(id: string, confirm: string): Promise<DeleteUserResult> {
  const { data } = await api.delete<DeleteUserResult>(`/api/v1/console/users/${id}`, { data: { confirm } });
  return data;
}

// ---------------------------------------------------------------------------
// 시스템
// ---------------------------------------------------------------------------

/** GET /api/v1/console/system — 런타임·저장 공간·배포 설정 점검 (모델을 새로 로드하지 않음) */
export async function fetchSystem(): Promise<SystemSnapshot> {
  const { data } = await api.get<SystemSnapshot>("/api/v1/console/system");
  return data;
}

/** POST /api/v1/console/system/cleanup?dry_run= — 보관 기간이 지난 업로드 파일 정리 */
export async function runCleanup(dryRun: boolean): Promise<CleanupResult> {
  const { data } = await api.post<CleanupResult>("/api/v1/console/system/cleanup", null, { params: { dry_run: dryRun } });
  return data;
}

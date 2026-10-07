/**
 * 운영 콘솔 전역 상태 (Zustand).
 *
 * page          : 현재 사이드바 메뉴
 * health / jobs : API 에서 받은 스냅샷
 * lastRefreshed : 마지막 성공 시각 (ISO 문자열)
 * auth / me     : 콘솔 접근 상태 (checking → in | login) · 누구로 들어왔는지
 */
import { create } from "zustand";
import type { ConsoleAuthStatus, ConsoleMe, ConsolePage, HealthResponse, JobResponse } from "../types";

interface ConsoleState {
  page: ConsolePage;
  health: HealthResponse | null;
  jobs: JobResponse[];
  loading: boolean;
  error: string | null;
  lastRefreshed: string | null;
  auth: ConsoleAuthStatus;
  me: ConsoleMe | null;
  authMessage: string | null;

  setPage: (page: ConsolePage) => void;
  setHealth: (health: HealthResponse | null) => void;
  setJobs: (jobs: JobResponse[]) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  markRefreshed: () => void;
  signedIn: (me: ConsoleMe) => void;
  requireLogin: (message?: string | null) => void;
}

export const useConsoleStore = create<ConsoleState>((set) => ({
  page: "dashboard",
  health: null,
  jobs: [],
  loading: false,
  error: null,
  lastRefreshed: null,
  auth: "checking",
  me: null,
  authMessage: null,

  setPage: (page) => set({ page }),
  setHealth: (health) => set({ health }),
  setJobs: (jobs) => set({ jobs }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  markRefreshed: () => set({ lastRefreshed: new Date().toISOString() }),
  signedIn: (me) => set({ auth: "in", me, authMessage: null }),
  requireLogin: (message = null) => set({ auth: "login", me: null, authMessage: message, jobs: [] }),
}));

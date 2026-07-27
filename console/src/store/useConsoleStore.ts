import { create } from "zustand";
import type { ConsolePage, HealthResponse, JobResponse } from "../types";

interface ConsoleState {
  page: ConsolePage;
  health: HealthResponse | null;
  jobs: JobResponse[];
  loading: boolean;
  error: string | null;
  lastRefreshed: string | null;

  setPage: (page: ConsolePage) => void;
  setHealth: (health: HealthResponse | null) => void;
  setJobs: (jobs: JobResponse[]) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  markRefreshed: () => void;
}

export const useConsoleStore = create<ConsoleState>((set) => ({
  page: "dashboard",
  health: null,
  jobs: [],
  loading: false,
  error: null,
  lastRefreshed: null,

  setPage: (page) => set({ page }),
  setHealth: (health) => set({ health }),
  setJobs: (jobs) => set({ jobs }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  markRefreshed: () => set({ lastRefreshed: new Date().toISOString() }),
}));

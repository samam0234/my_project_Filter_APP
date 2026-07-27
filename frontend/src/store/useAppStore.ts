import { create } from "zustand";
import type { ParsedPrompt, ProcessResultState } from "../types";

interface AppState {
  file: File | null;
  previewUrl: string | null;
  prompt: string;
  isProcessing: boolean;
  error: string | null;
  result: ProcessResultState | null;

  setFile: (file: File | null) => void;
  setPrompt: (prompt: string) => void;
  setProcessing: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setResult: (result: ProcessResultState | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  file: null,
  previewUrl: null,
  prompt: "사람만 남기고 배경 제거해줘",
  isProcessing: false,
  error: null,
  result: null,

  setFile: (file) => {
    const prev = get().previewUrl;
    if (prev) URL.revokeObjectURL(prev);
    set({
      file,
      previewUrl: file ? URL.createObjectURL(file) : null,
      result: null,
      error: null,
    });
  },
  setPrompt: (prompt) => set({ prompt }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  setError: (error) => set({ error }),
  setResult: (result) => set({ result }),
  reset: () => {
    const prev = get().previewUrl;
    if (prev) URL.revokeObjectURL(prev);
    set({
      file: null,
      previewUrl: null,
      isProcessing: false,
      error: null,
      result: null,
    });
  },
}));

export type { ParsedPrompt };

/**
 * 사용자 앱 전역 상태 (Zustand).
 *
 * - file / previewUrl : 업로드 선택 + 로컬 미리보기(Object URL)
 * - prompt            : 자연어 입력
 * - isProcessing      : 업로드·파이프라인 진행 중
 * - result            : 서버 처리 결과 (before/after URL 등)
 *
 * setFile / reset 시 이전 Object URL 을 revoke 해 메모리 누수를 막는다.
 */
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
  // 기본 프롬프트 예시 (휴리스틱 파서가 person + remove_bg 로 해석)
  prompt: "사람만 남기고 배경 제거해줘",
  isProcessing: false,
  error: null,
  result: null,

  setFile: (file) => {
    // 이전 미리보기 URL 해제
    const prev = get().previewUrl;
    if (prev) URL.revokeObjectURL(prev);
    set({
      file,
      previewUrl: file ? URL.createObjectURL(file) : null,
      // 새 파일이면 이전 결과/에러 초기화
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

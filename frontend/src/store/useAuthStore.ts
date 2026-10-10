/**
 * 로그인 상태 (Zustand).
 *
 * 세션 토큰은 HttpOnly 쿠키라 JS 가 읽을 수 없다 → 서버 /auth/me 결과만 보관한다.
 * status: "loading"(앱 시작 확인 중) · "guest" · "user"
 */
import { create } from "zustand";
import { fetchMe, loginRequest, logoutRequest, signupRequest } from "../api/client";
import type { AuthUser } from "../types";

type AuthStatus = "loading" | "guest" | "user";

interface AuthState {
  user: AuthUser | null;
  status: AuthStatus;
  refresh: () => Promise<void>;
  login: (username: string, password: string) => Promise<AuthUser>;
  signup: (body: { username: string; email: string; password: string; display_name?: string; agree_terms: boolean }) => Promise<AuthUser>;
  logout: () => Promise<void>;
  /** 서버가 돌려준 최신 사용자 정보로 바꾼다 (이름 수정 등) */
  setUser: (user: AuthUser) => void;
  /** 서버 세션이 이미 끝났을 때(전체 로그아웃 · 탈퇴) 화면 상태만 비로그인으로 */
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "loading",

  refresh: async () => {
    try {
      const user = await fetchMe();
      set({ user, status: user ? "user" : "guest" });
    } catch {
      // 서버 연결 실패 — 비로그인으로 두고 화면은 계속 쓰게 한다
      set({ user: null, status: "guest" });
    }
  },

  login: async (username, password) => {
    const user = await loginRequest(username, password);
    set({ user, status: "user" });
    return user;
  },

  signup: async (body) => {
    const user = await signupRequest(body);
    set({ user, status: "user" });
    return user;
  },

  setUser: (user) => set({ user, status: "user" }),

  clear: () => set({ user: null, status: "guest" }),

  logout: async () => {
    try {
      await logoutRequest();
    } finally {
      set({ user: null, status: "guest" });
    }
  },
}));

/** 화면에 보일 이름 */
export function displayName(user: AuthUser | null): string {
  return user?.display_name?.trim() || user?.username || "";
}

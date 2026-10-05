import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchMe: vi.fn(),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
  signupRequest: vi.fn(),
}));

import * as client from "../api/client";
import { displayName, useAuthStore } from "./useAuthStore";

const USER = { id: "u1", username: "keeper", email: "k@example.com", display_name: null };

beforeEach(() => {
  useAuthStore.setState({ user: null, status: "loading" });
});

describe("useAuthStore", () => {
  it("refresh — 세션 있으면 user, 없으면 guest", async () => {
    vi.mocked(client.fetchMe).mockResolvedValueOnce(USER as never);
    await useAuthStore.getState().refresh();
    expect(useAuthStore.getState().status).toBe("user");

    vi.mocked(client.fetchMe).mockResolvedValueOnce(null);
    await useAuthStore.getState().refresh();
    expect(useAuthStore.getState()).toMatchObject({ status: "guest", user: null });
  });

  it("refresh — 서버 연결 실패해도 화면은 비로그인으로 계속", async () => {
    vi.mocked(client.fetchMe).mockRejectedValueOnce(new Error("network"));
    await useAuthStore.getState().refresh();
    expect(useAuthStore.getState().status).toBe("guest");
  });

  it("login 실패는 상태를 바꾸지 않고 오류를 올린다", async () => {
    useAuthStore.setState({ status: "guest" });
    vi.mocked(client.loginRequest).mockRejectedValueOnce(new Error("401"));
    await expect(useAuthStore.getState().login("keeper", "bad")).rejects.toThrow("401");
    expect(useAuthStore.getState().status).toBe("guest");
  });

  it("logout 요청이 실패해도 로컬 상태는 비로그인", async () => {
    useAuthStore.setState({ user: USER as never, status: "user" });
    vi.mocked(client.logoutRequest).mockRejectedValueOnce(new Error("offline"));
    await expect(useAuthStore.getState().logout()).rejects.toThrow("offline");
    expect(useAuthStore.getState()).toMatchObject({ status: "guest", user: null });
  });

  it("displayName — 표시 이름 없으면 아이디", () => {
    expect(displayName(USER as never)).toBe("keeper");
    expect(displayName({ ...USER, display_name: "  킵 " } as never)).toBe("킵");
    expect(displayName(null)).toBe("");
  });
});

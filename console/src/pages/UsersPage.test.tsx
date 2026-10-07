import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchUsers: vi.fn(),
  unlockUser: vi.fn(),
  revokeUserSessions: vi.fn(),
  deleteUser: vi.fn(),
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));

import * as client from "../api/client";
import type { ConsoleUser } from "../types";
import { UsersPage } from "./UsersPage";

const user = (over: Partial<ConsoleUser>): ConsoleUser => ({
  id: "u1",
  username: "member_01",
  email: "m@example.com",
  display_name: null,
  created_at: "2026-10-01T00:00:00Z",
  last_login_at: null,
  locked: false,
  locked_until: null,
  failed_logins: 0,
  active_sessions: 0,
  job_count: 3,
  batch_count: 1,
  is_admin: false,
  ...over,
});

const BOSS = user({ id: "b1", username: "boss", email: "b@example.com", is_admin: true, active_sessions: 1 });
const LOCKED = user({ id: "u2", username: "locked_01", locked: true });

beforeEach(() => {
  vi.mocked(client.fetchUsers).mockResolvedValue({ items: [BOSS, LOCKED, user({})], total: 3, limit: 50, offset: 0 });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const row = async (name: string) => (await screen.findByText(name)).closest("tr") as HTMLElement;

describe("UsersPage (회원 관리)", () => {
  it("목록·검색, 관리자는 삭제 버튼이 없다", async () => {
    render(<UsersPage />);
    expect(within(await row("boss")).queryByText("삭제")).toBeNull();
    expect(within(await row("member_01")).getByText("삭제")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("회원 검색"), { target: { value: " member " } });
    fireEvent.click(screen.getByText("검색"));
    await waitFor(() => expect(client.fetchUsers).toHaveBeenLastCalledWith("member", 50, 0));
  });

  it("잠긴 계정 잠금 해제", async () => {
    vi.mocked(client.unlockUser).mockResolvedValue();
    render(<UsersPage />);
    fireEvent.click(within(await row("locked_01")).getByText("잠금 해제"));
    expect(await screen.findByText("locked_01 잠금 해제")).toBeTruthy();
    expect(client.unlockUser).toHaveBeenCalledWith("u2");
  });

  it("로그인 중인 계정 세션 끊기", async () => {
    vi.mocked(client.revokeUserSessions).mockResolvedValue(1);
    render(<UsersPage />);
    fireEvent.click(within(await row("boss")).getByText("로그아웃"));
    expect(await screen.findByText("boss 로그인 세션 1개 종료")).toBeTruthy();
  });

  it("삭제는 아이디를 다시 입력해야 버튼이 열린다", async () => {
    vi.mocked(client.deleteUser).mockResolvedValue({
      id: "u1", username: "member_01", jobs: 3, batches: 1, videos: 0, removed_dirs: 4, learning_unlinked: 2,
    });
    render(<UsersPage />);
    fireEvent.click(within(await row("member_01")).getByText("삭제"));
    const go = screen.getByText("영구 삭제").closest("button") as HTMLButtonElement;
    expect(go.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("삭제 확인 아이디"), { target: { value: "member_0" } });
    expect(go.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("삭제 확인 아이디"), { target: { value: "member_01" } });
    expect(go.disabled).toBe(false);
    fireEvent.click(go);
    expect(await screen.findByText(/member_01 삭제 — 작업 3 · 배치 1 · 영상 0 · 학습 데이터 연결 해제 2/)).toBeTruthy();
    expect(client.deleteUser).toHaveBeenCalledWith("u1", "member_01");
    expect(screen.queryByText("영구 삭제")).toBeNull();
  });

  it("서버 오류는 메시지로", async () => {
    vi.mocked(client.deleteUser).mockRejectedValue(new Error("관리자(CONSOLE_ADMINS) 계정은 지울 수 없습니다."));
    render(<UsersPage />);
    fireEvent.click(within(await row("member_01")).getByText("삭제"));
    fireEvent.change(screen.getByLabelText("삭제 확인 아이디"), { target: { value: "member_01" } });
    fireEvent.click(screen.getByText("영구 삭제"));
    expect((await screen.findByRole("alert")).textContent).toContain("지울 수 없습니다");
  });
});

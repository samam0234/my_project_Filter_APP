import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchConsoleMe: vi.fn(),
  consoleLogin: vi.fn(),
  consoleLogout: vi.fn(),
  setAuthRequiredHandler: vi.fn(),
  fetchHealth: vi.fn(),
  fetchJobs: vi.fn(),
  errorMessage: (e: unknown) =>
    (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String((e as Error)?.message ?? e),
}));

import * as client from "../api/client";
import App from "../App";
import { useConsoleStore } from "../store/useConsoleStore";

const denied = (status: number, detail: string) => Object.assign(new Error(detail), { response: { status, data: { detail } } });

async function login(username: string, password: string) {
  fireEvent.change(await screen.findByLabelText("아이디"), { target: { value: username } });
  fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: password } });
  fireEvent.click(screen.getByText("로그인"));
}

beforeEach(() => {
  useConsoleStore.setState({ auth: "checking", me: null, authMessage: null, page: "dashboard" });
  vi.mocked(client.fetchHealth).mockResolvedValue({ status: "ok", version: "t", phase: 2 });
  vi.mocked(client.fetchJobs).mockResolvedValue([]);
  vi.mocked(client.consoleLogout).mockResolvedValue();
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("콘솔 접근", () => {
  it("로그인이 필요하면 로그인 화면 → 관리자 로그인 후 콘솔", async () => {
    vi.mocked(client.fetchConsoleMe)
      .mockRejectedValueOnce(denied(401, "운영 콘솔 관리자 로그인이 필요합니다."))
      .mockResolvedValueOnce({ via: "admin", username: "boss" });
    vi.mocked(client.consoleLogin).mockResolvedValue();
    render(<App />);
    expect(await screen.findByText("관리자 로그인")).toBeTruthy();
    await login("boss", "pw-1234");
    expect(client.consoleLogin).toHaveBeenCalledWith("boss", "pw-1234");
    expect(await screen.findByText("관리자 boss")).toBeTruthy();
    expect(client.fetchHealth).toHaveBeenCalled(); // 들어온 뒤에야 데이터 요청
  });

  it("관리자가 아닌 계정은 들여보내지 않고 세션을 끊는다", async () => {
    vi.mocked(client.fetchConsoleMe)
      .mockRejectedValueOnce(denied(401, "로그인 필요"))
      .mockRejectedValueOnce(denied(403, "운영 콘솔 관리자 계정이 아닙니다."));
    vi.mocked(client.consoleLogin).mockResolvedValue();
    render(<App />);
    await login("member", "pw-1234");
    expect(await screen.findByText("운영 콘솔 관리자 계정이 아닙니다.")).toBeTruthy();
    expect(client.consoleLogout).toHaveBeenCalled();
    expect(client.fetchHealth).not.toHaveBeenCalled();
  });

  it("비밀번호가 틀리면 메시지만 보여 준다", async () => {
    vi.mocked(client.fetchConsoleMe).mockRejectedValueOnce(denied(401, "로그인 필요"));
    vi.mocked(client.consoleLogin).mockRejectedValue(denied(401, "아이디 또는 비밀번호가 올바르지 않습니다."));
    render(<App />);
    await login("boss", "wrong");
    expect(await screen.findByText("아이디 또는 비밀번호가 올바르지 않습니다.")).toBeTruthy();
    expect(client.fetchConsoleMe).toHaveBeenCalledTimes(1);
  });

  it("서버 PC 는 로그인 없이 들어가고 로그아웃 버튼이 없다", async () => {
    vi.mocked(client.fetchConsoleMe).mockResolvedValue({ via: "local", username: null });
    render(<App />);
    expect(await screen.findByText("서버 PC (로그인 없음)")).toBeTruthy();
    expect(screen.queryByText("로그아웃")).toBeNull();
  });

  it("관리자 로그아웃 → 로그인 화면", async () => {
    vi.mocked(client.fetchConsoleMe).mockResolvedValue({ via: "admin", username: "boss" });
    render(<App />);
    fireEvent.click(await screen.findByText("로그아웃"));
    await waitFor(() => expect(client.consoleLogout).toHaveBeenCalled());
    expect(await screen.findByText("관리자 로그인")).toBeTruthy();
  });
});

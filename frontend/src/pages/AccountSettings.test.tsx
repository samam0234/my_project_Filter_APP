import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  updateProfileRequest: vi.fn(),
  changePasswordRequest: vi.fn(),
  logoutAllRequest: vi.fn(),
  deleteAccountRequest: vi.fn(),
}));

vi.mock("../api/client", async (orig) => ({ ...(await orig<typeof import("../api/client")>()), ...api }));
vi.mock("../hooks/useApi", () => ({
  useJobs: () => ({
    data: [
      { job_id: "i1", prompt: "a", status: "ok", quality_score: 0.8, feedback_saved: false, kind: "image" },
      { job_id: "v1", prompt: "b", status: "failed", quality_score: 0, feedback_saved: false, kind: "video" },
    ],
    error: null,
    loading: false,
    reload: vi.fn(),
  }),
}));

import { useAuthStore } from "../store/useAuthStore";
import { AccountPage } from "./AccountPage";

const USER = { id: "u1", username: "member_01", email: "m@example.com", display_name: "멤버", created_at: "2026-10-01T00:00:00Z" };

beforeEach(() => {
  Object.values(api).forEach((f) => f.mockReset());
  useAuthStore.setState({ user: USER, status: "user" });
  window.history.replaceState(null, "", "/account");
});
afterEach(cleanup);

describe("AccountPage", () => {
  it("비로그인이면 로그인 안내를 보여 준다", () => {
    useAuthStore.setState({ user: null, status: "guest" });
    render(<AccountPage />);
    expect(screen.getByText("내 계정은 로그인 회원 전용이에요")).toBeTruthy();
  });

  it("내 정보 구역: 아이디 · 이메일 · 작업 개수를 보여 주고 이름을 바꾼다", async () => {
    api.updateProfileRequest.mockResolvedValue({ ...USER, display_name: "새이름" });
    render(<AccountPage />);
    expect(screen.getByText("member_01")).toBeTruthy();
    expect(screen.getByText("m@example.com")).toBeTruthy();
    expect(screen.getByText("그중 1건은 처리하지 못했어요.")).toBeTruthy();

    const save = screen.getByRole("button", { name: "저장" }) as HTMLButtonElement;
    expect(save.disabled).toBe(true); // 바꾸기 전에는 저장 불가
    fireEvent.change(screen.getByLabelText(/^표시 이름/), { target: { value: " 새이름 " } });
    fireEvent.click(save);
    await waitFor(() => expect(api.updateProfileRequest).toHaveBeenCalledWith("새이름"));
    await screen.findByText("표시 이름을 바꿨어요.");
    expect(useAuthStore.getState().user?.display_name).toBe("새이름");
  });

  it("구역 탭이 URL 의 tab 을 따라간다", () => {
    render(<AccountPage />);
    fireEvent.click(screen.getByRole("tab", { name: /보안/ }));
    expect(window.location.search).toBe("?tab=security");
    expect(screen.getByText("비밀번호 변경")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: /내 정보/ }));
    expect(window.location.search).toBe("");
  });

  it("비밀번호 변경: 규칙·확인이 맞아야 보내고, 성공하면 입력을 비운다", async () => {
    api.changePasswordRequest.mockResolvedValue({ ok: true, message: "비밀번호를 바꿨습니다." });
    window.history.replaceState(null, "", "/account?tab=security");
    render(<AccountPage />);
    const submit = screen.getByRole("button", { name: "비밀번호 바꾸기" }) as HTMLButtonElement;
    fireEvent.change(screen.getByLabelText("현재 비밀번호"), { target: { value: "oldpass2026" } });
    fireEvent.change(screen.getByLabelText(/^새 비밀번호(?! 확인)/), { target: { value: "short" } });
    expect(screen.getByText("8~64자로 입력해 주세요.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText(/^새 비밀번호(?! 확인)/), { target: { value: "newpass2026" } });
    fireEvent.change(screen.getByLabelText(/^새 비밀번호 확인/), { target: { value: "newpass2027" } });
    expect(screen.getByText("새 비밀번호와 같지 않아요.")).toBeTruthy();
    expect(submit.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText(/^새 비밀번호 확인/), { target: { value: "newpass2026" } });
    fireEvent.click(submit);
    await waitFor(() => expect(api.changePasswordRequest).toHaveBeenCalledWith("oldpass2026", "newpass2026"));
    await screen.findByText("비밀번호를 바꿨습니다.");
    expect((screen.getByLabelText("현재 비밀번호") as HTMLInputElement).value).toBe("");
  });

  it("모든 기기에서 로그아웃하면 비로그인 상태가 되고 로그인 화면으로 간다", async () => {
    api.logoutAllRequest.mockResolvedValue(undefined);
    window.history.replaceState(null, "", "/account?tab=security");
    render(<AccountPage />);
    fireEvent.click(screen.getByRole("button", { name: /모든 기기에서 로그아웃/ }));
    await waitFor(() => expect(useAuthStore.getState().status).toBe("guest"));
    expect(window.location.pathname).toBe("/login");
  });

  it("탈퇴: 아이디를 정확히 입력해야 버튼이 켜지고, 실패하면 로그인 상태를 유지한다", async () => {
    api.deleteAccountRequest.mockRejectedValueOnce(new Error("비밀번호가 올바르지 않습니다."));
    window.history.replaceState(null, "", "/account?tab=data");
    render(<AccountPage />);
    const btn = screen.getByRole("button", { name: /계정 탈퇴/ }) as HTMLButtonElement;
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "wrongpass1" } });
    fireEvent.change(screen.getByLabelText(/아이디\(member_01\)/), { target: { value: "other" } });
    expect(btn.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText(/아이디\(member_01\)/), { target: { value: "Member_01" } });
    expect(btn.disabled).toBe(false);
    fireEvent.click(btn);
    await waitFor(() => expect(api.deleteAccountRequest).toHaveBeenCalledWith("wrongpass1", "Member_01"));
    await screen.findByRole("alert");
    expect(useAuthStore.getState().status).toBe("user");
  });

  it("탈퇴가 끝나면 비로그인 상태로 홈에 간다", async () => {
    api.deleteAccountRequest.mockResolvedValue({ ok: true, message: "탈퇴했습니다." });
    window.history.replaceState(null, "", "/account?tab=data");
    render(<AccountPage />);
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "rightpass1" } });
    fireEvent.change(screen.getByLabelText(/아이디\(member_01\)/), { target: { value: "member_01" } });
    fireEvent.click(screen.getByRole("button", { name: /계정 탈퇴/ }));
    await waitFor(() => expect(useAuthStore.getState().status).toBe("guest"));
    expect(window.location.pathname).toBe("/");
  });
});

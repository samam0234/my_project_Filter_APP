import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ signupVerifyRequest: vi.fn(), signupResendRequest: vi.fn() }));
vi.mock("../../api/client", async (orig) => ({ ...(await orig<typeof import("../../api/client")>()), ...api }));

import { useAuthStore } from "../../store/useAuthStore";
import { SignupVerifyPage, formatSerial } from "./SignupVerifyPage";

const USER = { id: "u1", username: "newbie_01", email: "n@example.com" };

beforeEach(() => {
  api.signupVerifyRequest.mockReset().mockResolvedValue(USER);
  api.signupResendRequest.mockReset().mockResolvedValue({ ok: true, message: "일련번호를 다시 보냈어요.", verification_required: true });
  useAuthStore.setState({ user: null, status: "guest" });
  window.history.replaceState(null, "", "/signup/verify?email=n%40example.com");
});
afterEach(cleanup);

const codeInput = () => screen.getByLabelText(/^일련번호/) as HTMLInputElement;
const submit = () => screen.getByRole("button", { name: /인증하고 가입 완료/ }) as HTMLButtonElement;

describe("formatSerial", () => {
  it("대소문자 · 공백 · 하이픈을 정리해 4-4 로 맞추고 8글자까지만 받는다", () => {
    expect(formatSerial("k7qm")).toBe("K7QM");
    expect(formatSerial("k7qm2")).toBe("K7QM-2");
    expect(formatSerial(" k7qm-2xwd ")).toBe("K7QM-2XWD");
    expect(formatSerial("K7QM-2XWD-9999")).toBe("K7QM-2XWD");
  });
});

describe("회원가입 2단계 — 메일 일련번호 입력", () => {
  it("링크의 이메일을 안내하고 8글자를 다 채워야 가입 완료 버튼이 켜진다", () => {
    render(<SignupVerifyPage />);
    expect(screen.getByText("n@example.com")).toBeTruthy();
    expect(screen.queryByLabelText("이메일")).toBeNull(); // 링크로 왔으면 이메일은 묻지 않는다
    expect(submit().disabled).toBe(true);
    fireEvent.change(codeInput(), { target: { value: "k7qm2x" } });
    expect(codeInput().value).toBe("K7QM-2X");
    expect(submit().disabled).toBe(true);
    fireEvent.change(codeInput(), { target: { value: "k7qm2xwd" } });
    expect(codeInput().value).toBe("K7QM-2XWD");
    expect(submit().disabled).toBe(false);
  });

  it("인증에 성공하면 로그인 상태가 되고 next(없으면 홈)로 간다", async () => {
    window.history.replaceState(null, "", "/signup/verify?email=n%40example.com&next=%2Fstudio");
    render(<SignupVerifyPage />);
    fireEvent.change(codeInput(), { target: { value: "K7QM2XWD" } });
    fireEvent.click(submit());
    await waitFor(() => expect(api.signupVerifyRequest).toHaveBeenCalledWith("n@example.com", "K7QM-2XWD"));
    await waitFor(() => expect(useAuthStore.getState().status).toBe("user"));
    expect(useAuthStore.getState().user?.username).toBe("newbie_01");
    expect(window.location.pathname).toBe("/studio");
  });

  it("틀리면 서버 안내(남은 횟수)를 보여 주고 가입 상태는 그대로다", async () => {
    api.signupVerifyRequest.mockRejectedValue(new Error("일련번호가 달라요. 4번 더 틀리면 새로 받아야 해요."));
    render(<SignupVerifyPage />);
    fireEvent.change(codeInput(), { target: { value: "AAAABBBB" } });
    fireEvent.click(submit());
    expect((await screen.findByRole("alert")).textContent).toContain("4번 더 틀리면");
    expect(useAuthStore.getState().status).toBe("guest");
  });

  it("일련번호 다시 받기 — 안내를 보여 주고 입력을 비우고 잠시 막는다", async () => {
    render(<SignupVerifyPage />);
    fireEvent.change(codeInput(), { target: { value: "AAAABBBB" } });
    fireEvent.click(screen.getByRole("button", { name: /일련번호 다시 받기/ }));
    await waitFor(() => expect(api.signupResendRequest).toHaveBeenCalledWith("n@example.com"));
    await screen.findByText("일련번호를 다시 보냈어요.");
    expect(codeInput().value).toBe("");
    expect((screen.getByRole("button", { name: /일련번호 다시 받기 \(\d+초\)/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("링크 없이 직접 열면 이메일도 입력받는다", () => {
    window.history.replaceState(null, "", "/signup/verify");
    render(<SignupVerifyPage />);
    const email = screen.getByLabelText("이메일") as HTMLInputElement;
    fireEvent.change(codeInput(), { target: { value: "K7QM2XWD" } });
    expect(submit().disabled).toBe(true); // 이메일이 비었다
    fireEvent.change(email, { target: { value: "n@example.com" } });
    expect(submit().disabled).toBe(false);
  });

  it("메일이 안 나가는 개발 서버(dev=1)면 실제 메일이 가지 않았다고 알려 준다", () => {
    window.history.replaceState(null, "", "/signup/verify?email=n%40example.com&dev=1");
    render(<SignupVerifyPage />);
    expect(screen.getByRole("alert").textContent).toContain("메일이 실제로 가지 않았어요");
    cleanup();
    window.history.replaceState(null, "", "/signup/verify?email=n%40example.com");
    render(<SignupVerifyPage />);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

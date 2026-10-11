import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const signupStart = vi.hoisted(() => vi.fn());
vi.mock("../../api/client", async (orig) => ({ ...(await orig<typeof import("../../api/client")>()), signupStartRequest: signupStart }));

import { useAuthStore } from "../../store/useAuthStore";
import { PrivacyPage } from "../legal/PrivacyPage";
import { TermsPage } from "../legal/TermsPage";
import { SignupPage } from "./SignupPage";

beforeEach(() => {
  signupStart.mockReset().mockResolvedValue({ ok: true, message: "보냈어요", verification_required: true, email: "n@example.com" });
  useAuthStore.setState({ user: null, status: "guest" });
  window.history.replaceState(null, "", "/signup");
});
afterEach(cleanup);

function fill() {
  const [id, mail] = screen.getAllByRole("textbox");
  fireEvent.change(id, { target: { value: "new_user" } });
  fireEvent.change(mail, { target: { value: "n@example.com" } });
  const [pw, confirm] = Array.from(document.querySelectorAll<HTMLInputElement>("input[type=password]"));
  fireEvent.change(pw, { target: { value: "Passw0rd2026" } });
  fireEvent.change(confirm, { target: { value: "Passw0rd2026" } });
}

describe("회원가입 동의", () => {
  it("만 14세 · 약관 · 개인정보 동의 체크 없이는 가입 요청을 보내지 않는다", async () => {
    render(<SignupPage />);
    fill();
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    expect(await screen.findByText("가입하려면 동의가 필요해요.")).toBeTruthy();
    expect(signupStart).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    await vi.waitFor(() => expect(signupStart).toHaveBeenCalledTimes(1));
    expect(signupStart.mock.calls[0][0]).toMatchObject({ username: "new_user", agree_terms: true });
  });

  it("약관 · 개인정보 처리방침으로 가는 링크가 있다", () => {
    render(<SignupPage />);
    expect(screen.getAllByRole("link", { name: "이용약관" })[0].getAttribute("href")).toBe("/terms");
    expect(screen.getAllByRole("link", { name: "개인정보 처리방침" })[0].getAttribute("href")).toBe("/privacy");
  });
});

describe("회원가입 1단계 → 이메일 인증", () => {
  it("가입하기를 누르면 계정을 만들지 않고 메일 인증 화면(이메일 포함)으로 보낸다", async () => {
    window.history.replaceState(null, "", "/signup?next=%2Fstudio");
    render(<SignupPage />);
    fill();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    await vi.waitFor(() => expect(window.location.pathname).toBe("/signup/verify"));
    const q = new URLSearchParams(window.location.search);
    expect(q.get("email")).toBe("n@example.com");
    expect(q.get("next")).toBe("/studio");
    expect(useAuthStore.getState().status).toBe("guest"); // 인증 전에는 로그인 상태가 아니다
  });

  it("서버가 인증을 끈 경우(개발)에는 바로 가입된 로그인 상태가 된다", async () => {
    signupStart.mockResolvedValue({ ok: true, message: "가입했습니다.", verification_required: false, user: { id: "u", username: "new_user", email: "n@example.com" } });
    render(<SignupPage />);
    fill();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    await vi.waitFor(() => expect(useAuthStore.getState().status).toBe("user"));
    expect(window.location.pathname).toBe("/");
  });

  it("서버 오류(중복 아이디 등)는 그대로 보여 주고 인증 화면으로 가지 않는다", async () => {
    signupStart.mockRejectedValue(new Error("이미 사용 중인 아이디입니다."));
    render(<SignupPage />);
    fill();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    await screen.findByRole("alert");
    expect(window.location.pathname).toBe("/signup");
  });
});

describe("개인정보 처리방침 · 이용약관", () => {
  it("실제 동작과 같은 보관 기간 · 비로그인 미저장을 안내하고, 운영자 정보가 없으면 설정 필요로 보인다", () => {
    render(<PrivacyPage />);
    expect(screen.getAllByText(/24시간 뒤 자동 삭제/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/저장하지 않음/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/설정 필요/).length).toBeGreaterThan(0);
    cleanup();
    render(<TermsPage />);
    expect(screen.getByText(/컷앤킵 이용약관/)).toBeTruthy();
  });
});

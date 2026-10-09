import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "../../store/useAuthStore";
import { PrivacyPage } from "../legal/PrivacyPage";
import { TermsPage } from "../legal/TermsPage";
import { SignupPage } from "./SignupPage";

const signup = vi.fn();

beforeEach(() => {
  signup.mockReset().mockResolvedValue({ id: "u", username: "new_user", email: "n@example.com" });
  useAuthStore.setState({ user: null, status: "guest", signup } as never);
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
    expect(signup).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /가입하기/ }));
    await vi.waitFor(() => expect(signup).toHaveBeenCalledTimes(1));
    expect(signup.mock.calls[0][0]).toMatchObject({ username: "new_user", agree_terms: true });
  });

  it("약관 · 개인정보 처리방침으로 가는 링크가 있다", () => {
    render(<SignupPage />);
    expect(screen.getAllByRole("link", { name: "이용약관" })[0].getAttribute("href")).toBe("/terms");
    expect(screen.getAllByRole("link", { name: "개인정보 처리방침" })[0].getAttribute("href")).toBe("/privacy");
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

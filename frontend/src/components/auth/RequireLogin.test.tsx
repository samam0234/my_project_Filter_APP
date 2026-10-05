import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore } from "../../store/useAuthStore";
import { RequireLogin } from "./RequireLogin";

afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
});

function renderGate() {
  return render(
    <RequireLogin title="배치 처리" reason="회원만 쓸 수 있어요">
      <p>비밀 화면</p>
    </RequireLogin>,
  );
}

describe("RequireLogin (회원 전용 화면)", () => {
  it("비로그인 — 내용 대신 로그인 안내, 돌아올 주소(next) 포함", () => {
    window.history.replaceState(null, "", "/batch?tab=new");
    useAuthStore.setState({ user: null, status: "guest" });
    renderGate();
    expect(screen.queryByText("비밀 화면")).toBeNull();
    const login = screen.getByText("로그인").closest("a");
    expect(login?.getAttribute("href")).toBe(`/login?next=${encodeURIComponent("/batch?tab=new")}`);
    expect(screen.getByText("작업실").closest("a")?.getAttribute("href")).toBe("/studio");
  });

  it("확인 중 — 로딩", () => {
    useAuthStore.setState({ user: null, status: "loading" });
    renderGate();
    expect(screen.getByText("로그인 상태 확인 중…")).toBeTruthy();
  });

  it("로그인 — 내용 표시", () => {
    useAuthStore.setState({ user: { id: "u", username: "k", email: "k@x.com" } as never, status: "user" });
    renderGate();
    expect(screen.getByText("비밀 화면")).toBeTruthy();
  });
});

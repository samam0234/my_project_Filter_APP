import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../hooks/useApi", () => ({ useHealth: () => ({ online: true, health: null }) }));

import { useAuthStore } from "../../store/useAuthStore";
import { AppLayout } from "./AppLayout";

const USER = { id: "u1", username: "member_01", email: "m@example.com", display_name: "멤버" };

beforeEach(() => {
  useAuthStore.setState({ user: USER, status: "user" });
  window.history.replaceState(null, "", "/studio");
});
afterEach(cleanup);

describe("AppLayout 프로필 메뉴", () => {
  it("헤더 메뉴에는 작업 기록 링크가 없다 (내 계정 안으로 옮겨졌다)", () => {
    render(<AppLayout>x</AppLayout>);
    const links = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    expect(links).not.toContain("/history");
    expect(links).not.toContain("/account?tab=history"); // 프로필 메뉴를 열기 전에는 보이지 않는다
  });

  it("프로필을 누르면 이름 · 이메일과 내 계정 · 작업 기록 · 로그아웃을 연다", () => {
    render(<AppLayout>x</AppLayout>);
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "내 계정 메뉴" }));
    expect(screen.getByRole("menu").textContent).toContain("m@example.com");
    expect(screen.getByRole("menuitem", { name: /내 계정/ }).getAttribute("href")).toBe("/account");
    expect(screen.getByRole("menuitem", { name: /작업 기록/ }).getAttribute("href")).toBe("/account?tab=history");
    expect(screen.getByRole("menuitem", { name: /로그아웃/ })).toBeTruthy();
  });

  it("Esc 나 바깥 클릭, 화면 이동으로 닫힌다", () => {
    render(<AppLayout>x</AppLayout>);
    const open = () => fireEvent.click(screen.getByRole("button", { name: "내 계정 메뉴" }));
    open();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    open();
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole("menu")).toBeNull();
    open();
    fireEvent.click(screen.getByRole("menuitem", { name: /내 계정/ }));
    expect(screen.queryByRole("menu")).toBeNull();
    expect(window.location.pathname).toBe("/account");
  });
});

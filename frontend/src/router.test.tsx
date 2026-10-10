import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Link, matchRoute, navigate, usePathname } from "./router";

afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
});

describe("router", () => {
  it("matchRoute — 파라미터 · 끝 슬래시 · 불일치", () => {
    expect(matchRoute("/jobs/:id", "/jobs/abc")).toEqual({ id: "abc" });
    expect(matchRoute("/jobs/:id", "/jobs/a%20b/")).toEqual({ id: "a b" });
    expect(matchRoute("/jobs/:id", "/jobs")).toBeNull();
    expect(matchRoute("/", "/")).toEqual({});
  });

  it("navigate 와 Link 클릭이 구독 중인 화면을 바꾼다", () => {
    function Where() {
      return (
        <div>
          <span data-testid="path">{usePathname()}</span>
          <Link to="/history">기록</Link>
        </div>
      );
    }
    render(<Where />);
    expect(screen.getByTestId("path").textContent).toBe("/");
    act(() => navigate("/studio"));
    expect(screen.getByTestId("path").textContent).toBe("/studio");
    fireEvent.click(screen.getByText("기록"));
    expect(screen.getByTestId("path").textContent).toBe("/history");
  });
});

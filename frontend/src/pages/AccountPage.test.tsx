import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JobResponse } from "../types";

const JOBS: JobResponse[] = [
  { job_id: "i1", prompt: "사진 작업", status: "ok", quality_score: 0.8, feedback_saved: false, kind: "image", thumb_url: "/api/v1/files/i1/thumb" },
  { job_id: "v1", prompt: "영상 작업", status: "ok", quality_score: 0, feedback_saved: false, kind: "video", thumb_url: "/api/v1/files/v1/thumb" },
  { job_id: "g1", prompt: "GIF 작업", status: "ok", quality_score: 0, feedback_saved: false, kind: "gif", thumb_url: "/api/v1/files/g1/thumb" },
  { job_id: "o1", prompt: "예전 사진", status: "failed", quality_score: 0, feedback_saved: false },
];

vi.mock("../hooks/useApi", () => ({
  useJobs: () => ({ data: JOBS, error: null, loading: false, reload: vi.fn() }),
}));

import { useAuthStore } from "../store/useAuthStore";
import { AccountPage } from "./AccountPage";

beforeEach(() => {
  useAuthStore.setState({ user: { id: "u", username: "m", email: "m@x" }, status: "user" });
  window.history.replaceState(null, "", "/account?tab=history");
});
afterEach(cleanup);

const titles = () => screen.queryAllByText(/작업$|예전 사진/).map((el) => el.textContent);

describe("AccountPage — 작업 기록 구역", () => {
  it("사진·영상·GIF 를 함께 보여 주고 종류 배지와 썸네일을 쓴다", () => {
    render(<AccountPage />);
    expect(titles()).toEqual(["사진 작업", "영상 작업", "GIF 작업", "예전 사진"]);
    const video = screen.getByText("영상 작업").closest("a") as HTMLElement;
    expect(within(video).getByText("영상")).toBeTruthy();
    expect((within(video).getByRole("img") as HTMLImageElement).src).toContain("/api/v1/files/v1/thumb");
    expect(within(screen.getByText("GIF 작업").closest("a") as HTMLElement).getByText("GIF")).toBeTruthy();
  });

  it("종류 필터 — kind 가 없는 예전 작업은 사진으로 센다", () => {
    render(<AccountPage />);
    const kinds = screen.getByRole("tablist", { name: "작업 종류" });
    expect(within(kinds).getByRole("tab", { name: /사진/ }).textContent).toContain("2");
    fireEvent.click(within(kinds).getByRole("tab", { name: /영상/ }));
    expect(window.location.search).toBe("?tab=history&kind=video");
    expect(titles()).toEqual(["영상 작업"]);
    fireEvent.click(within(kinds).getByRole("tab", { name: /사진/ }));
    expect(titles()).toEqual(["사진 작업", "예전 사진"]);
  });
});

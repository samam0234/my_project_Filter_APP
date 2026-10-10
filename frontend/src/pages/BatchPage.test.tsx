import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  createBatch: vi.fn(),
  getBatch: vi.fn(),
  listBatches: vi.fn(),
  downloadFile: vi.fn(),
  resolveAssetUrl: (u?: string | null) => u ?? undefined,
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));

import * as client from "../api/client";
import { useAuthStore } from "../store/useAuthStore";
import { BatchPage } from "./BatchPage";

const SUMMARY = {
  job_id: "b1234567890",
  status: "done",
  progress: 1,
  total: 2,
  completed: 2,
  message: "완료 (실패 1/2)",
  prompt: "왼쪽 사람만 남기고",
  created_at: "2026-10-07T00:00:00Z",
};
const DONE = {
  ...SUMMARY,
  download_url: "/api/v1/batch/b1234567890/download",
  item_results: [
    { index: 0, filename: "a.jpg", status: "ok", before_url: "/b/0/before", after_url: "/b/0/after" },
    { index: 1, filename: "b.jpg", status: "failed", message: "디코딩 실패", before_url: "/b/1/before", after_url: null },
  ],
};

beforeEach(() => {
  useAuthStore.setState({ user: { id: "u", username: "k", email: "k@x.com" } as never, status: "user" });
  vi.mocked(client.listBatches).mockResolvedValue([SUMMARY]);
  vi.mocked(client.getBatch).mockResolvedValue(DONE as never);
  vi.mocked(client.downloadFile).mockResolvedValue();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("BatchPage (회원 전용 배치)", () => {
  it("낡은 '준비 중' 안내 대신 24시간 보관 안내를 보여 준다", async () => {
    render(<BatchPage />);
    expect(await screen.findByText(/24시간/)).toBeTruthy();
    expect(screen.queryByText(/준비 중인 기능/)).toBeNull();
  });

  it("내 배치를 고르면 항목별 결과 · 실패 항목 · zip 버튼이 나온다", async () => {
    render(<BatchPage />);
    fireEvent.click(await screen.findByText("왼쪽 사람만 남기고"));
    expect(await screen.findByText("a.jpg")).toBeTruthy();
    expect(screen.getByText("처리하지 못했어요")).toBeTruthy();
    expect(screen.getByText("디코딩 실패")).toBeTruthy();
    expect(screen.getAllByRole("img").length).toBe(3); // a 원본·결과 + b 원본 (b 결과는 없음)
    fireEvent.click(screen.getByText("결과 모두 받기 (zip)"));
    await waitFor(() =>
      expect(client.downloadFile).toHaveBeenCalledWith("/api/v1/batch/b1234567890/download", "cutnkeep_batch_b1234567.zip"),
    );
  });

  it("처리 중이면 2초마다 다시 가져오고, 끝나면 멈춘다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(client.getBatch)
      .mockResolvedValueOnce({ ...DONE, status: "running", progress: 0.5, completed: 1, download_url: null, item_results: [] } as never)
      .mockResolvedValue(DONE as never);
    render(<BatchPage />);
    fireEvent.click(await screen.findByText("왼쪽 사람만 남기고"));
    expect(await screen.findByText("처리 중")).toBeTruthy();
    expect(client.getBatch).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect(await screen.findByText("a.jpg")).toBeTruthy();
    expect(client.getBatch).toHaveBeenCalledTimes(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    expect(client.getBatch).toHaveBeenCalledTimes(2); // 완료 뒤에는 더 부르지 않음
  });

  it("조회 오류는 화면에 보이고 목록은 유지된다", async () => {
    vi.mocked(client.getBatch).mockRejectedValue(new Error("서버 오류"));
    render(<BatchPage />);
    fireEvent.click(await screen.findByText("왼쪽 사람만 남기고"));
    expect(await screen.findByText("서버 오류")).toBeTruthy();
    expect(screen.getByText("내 배치")).toBeTruthy();
  });

  it("비로그인은 잠금 안내", () => {
    useAuthStore.setState({ user: null, status: "guest" });
    render(<BatchPage />);
    expect(screen.getByText("배치는 로그인 회원 전용이에요")).toBeTruthy();
  });
});

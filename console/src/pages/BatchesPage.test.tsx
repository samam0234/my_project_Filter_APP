import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({ fetchBatches: vi.fn() }));

import * as client from "../api/client";
import { BatchesPage } from "./BatchesPage";

const ROW = {
  job_id: "abcdef0123456789",
  user_id: "user-uuid-1234",
  status: "done",
  progress: 1,
  total: 5,
  completed: 5,
  failed: 2,
  message: "완료 (실패 2/5)",
  prompt: "왼쪽 사람만 남기고",
  created_at: "2026-10-07T00:00:00Z",
};

beforeEach(() => {
  vi.mocked(client.fetchBatches).mockResolvedValue([ROW]); // 반환값을 두면 vitest 가 정리 함수로 호출한다
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("BatchesPage (콘솔 배치 현황)", () => {
  it("전체 배치 목록과 실패 수를 보여 주고 이미지는 노출하지 않는다", async () => {
    render(<BatchesPage />);
    expect(await screen.findByText("왼쪽 사람만 남기고")).toBeTruthy();
    expect(screen.getByText("abcdef012345…")).toBeTruthy();
    expect(screen.getByText("user-uui")).toBeTruthy(); // 회원 ID 앞 8자
    expect(screen.getByText("5/5 · 100%")).toBeTruthy();
    expect(screen.getAllByText("2").length).toBeGreaterThan(0); // 실패 수
    expect(screen.queryAllByRole("img").length).toBe(0);
  });

  it("비어 있으면 안내", async () => {
    vi.mocked(client.fetchBatches).mockResolvedValue([]);
    render(<BatchesPage />);
    expect(await screen.findByText("아직 등록된 배치가 없습니다.")).toBeTruthy();
  });

  it("진행 중인 배치가 있으면 5초마다 갱신하고, 끝나면 멈춘다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(client.fetchBatches)
      .mockResolvedValueOnce([{ ...ROW, status: "running", progress: 0.4, completed: 2, failed: 0 }])
      .mockResolvedValue([ROW]);
    render(<BatchesPage />);
    expect(await screen.findByText("2/5 · 40%")).toBeTruthy();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5100);
    });
    expect(await screen.findByText("5/5 · 100%")).toBeTruthy();
    const calls = vi.mocked(client.fetchBatches).mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(20_000);
    });
    expect(vi.mocked(client.fetchBatches).mock.calls.length).toBe(calls); // 완료 뒤에는 더 부르지 않음
  });

  it("조회 오류를 안내한다", async () => {
    vi.mocked(client.fetchBatches).mockRejectedValue(new Error("Network Error"));
    render(<BatchesPage />);
    expect(await screen.findByText("Network Error")).toBeTruthy();
  });
});

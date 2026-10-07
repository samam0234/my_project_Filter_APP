import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  processVideo: vi.fn(),
  downloadFile: vi.fn(),
  saveBlob: vi.fn(),
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));

import * as client from "../api/client";
import { useAuthStore } from "../store/useAuthStore";
import { VideoPage } from "./VideoPage";

const FILE = () => new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });

async function pickAndRun() {
  const input = document.querySelector("input[type=file]") as HTMLInputElement;
  fireEvent.change(input, { target: { files: [FILE()] } });
  const run = await screen.findByText("영상 처리 시작");
  await waitFor(() => expect((run.closest("button") as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(run);
}

beforeEach(() => useAuthStore.setState({ user: null, status: "guest" }));
afterEach(cleanup);

describe("VideoPage", () => {
  it("비로그인: 서버에 저장되지 않는다는 안내와 결과 저장(blob)", async () => {
    const blob = new Blob(["avi"]);
    vi.mocked(client.processVideo).mockResolvedValue({ kind: "download", blob, frames: 30, held: 4 });
    render(<VideoPage />);
    expect(screen.getByText(/아무것도 남기지 않아요/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/30프레임 처리/)).toBeTruthy();
    expect(screen.getByText(/서버에 저장되지 않았어요/)).toBeTruthy();
    fireEvent.click(screen.getByText("결과 저장 (avi)"));
    expect(client.saveBlob).toHaveBeenCalledWith(blob, "cutnkeep_video.avi");
    expect(client.processVideo).toHaveBeenCalledWith(expect.any(File), "사람만 남기고 배경 블러");
  });

  it("회원: 보관본은 인증 다운로드로 받는다", async () => {
    useAuthStore.setState({ user: { id: "u", username: "k", email: "k@x.com" } as never, status: "user" });
    vi.mocked(client.processVideo).mockResolvedValue({ kind: "saved", jobId: "j1", url: "/api/v1/video/j1", frames: 12, held: 0 });
    vi.mocked(client.downloadFile).mockResolvedValue();
    render(<VideoPage />);
    expect(screen.getByText(/24시간 보관돼/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/서버에 보관됨/)).toBeTruthy();
    fireEvent.click(screen.getByText("결과 저장 (avi)"));
    await waitFor(() => expect(client.downloadFile).toHaveBeenCalledWith("/api/v1/video/j1", "cutnkeep_video.avi"));
  });

  it("처리 오류는 메시지로 보여 주고 다시 시도할 수 있다", async () => {
    vi.mocked(client.processVideo).mockRejectedValue(new Error("영상이 최대 크기를 초과합니다"));
    render(<VideoPage />);
    await pickAndRun();
    expect(await screen.findByText("영상이 최대 크기를 초과합니다")).toBeTruthy();
    expect((screen.getByText("영상 처리 시작").closest("button") as HTMLButtonElement).disabled).toBe(false);
  });

  it("영상을 고르기 전에는 시작할 수 없다", () => {
    render(<VideoPage />);
    expect((screen.getByText("영상 처리 시작").closest("button") as HTMLButtonElement).disabled).toBe(true);
  });
});

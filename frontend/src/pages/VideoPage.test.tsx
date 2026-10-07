import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  processVideo: vi.fn(),
  fetchBlob: vi.fn(),
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

beforeEach(() => {
  useAuthStore.setState({ user: null, status: "guest" });
  // jsdom 에는 object URL 이 없다
  URL.createObjectURL = vi.fn(() => "blob:preview");
  URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("VideoPage", () => {
  it("비로그인: 결과를 바로 재생하고 webm 으로 저장(서버에 남지 않음)", async () => {
    const blob = new Blob(["webm"]);
    vi.mocked(client.processVideo).mockResolvedValue({ kind: "download", blob, format: "webm", frames: 30, held: 4 });
    render(<VideoPage />);
    expect(screen.getByText(/아무것도 남기지 않아요/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/30프레임 처리/)).toBeTruthy();
    expect(screen.getByText(/서버에 저장되지 않았어요/)).toBeTruthy();
    const player = (await screen.findByLabelText("처리 결과 영상")) as HTMLVideoElement;
    expect(player.getAttribute("src")).toBe("blob:preview");
    expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
    fireEvent.click(screen.getByText("결과 저장 (webm)"));
    expect(client.saveBlob).toHaveBeenCalledWith(blob, "cutnkeep_video.webm");
    expect(client.processVideo).toHaveBeenCalledWith(expect.any(File), "사람만 남기고 배경 블러");
  });

  it("회원: 보관본을 인증 요청으로 받아 재생·저장한다", async () => {
    useAuthStore.setState({ user: { id: "u", username: "k", email: "k@x.com" } as never, status: "user" });
    const blob = new Blob(["webm"]);
    vi.mocked(client.processVideo).mockResolvedValue({
      kind: "saved", jobId: "j1", url: "/api/v1/video/j1", format: "webm", frames: 12, held: 0,
    });
    vi.mocked(client.fetchBlob).mockResolvedValue(blob);
    render(<VideoPage />);
    expect(screen.getByText(/24시간 보관돼/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/서버에 보관됨/)).toBeTruthy();
    expect(client.fetchBlob).toHaveBeenCalledWith("/api/v1/video/j1");
    expect(await screen.findByLabelText("처리 결과 영상")).toBeTruthy();
    const save = screen.getByText("결과 저장 (webm)").closest("button") as HTMLButtonElement;
    await waitFor(() => expect(save.disabled).toBe(false));
    fireEvent.click(save);
    expect(client.saveBlob).toHaveBeenCalledWith(blob, "cutnkeep_video.webm");
  });

  it("avi 로 온 결과는 재생기 대신 내려받기 안내", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ kind: "download", blob: new Blob(["avi"]), format: "avi", frames: 3, held: 0 });
    render(<VideoPage />);
    await pickAndRun();
    expect(await screen.findByText(/webm 인코더가 없어 avi 로/)).toBeTruthy();
    expect(screen.queryByLabelText("처리 결과 영상")).toBeNull();
    expect(screen.getByText("결과 저장 (avi)")).toBeTruthy();
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

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  processVideo: vi.fn(),
  fetchBlob: vi.fn(),
  saveBlob: vi.fn(),
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));
vi.mock("../utils/videoStore", () => ({
  saveVideo: vi.fn(),
  loadVideo: vi.fn(),
  clearVideo: vi.fn(),
}));

import * as client from "../api/client";
import { useAuthStore } from "../store/useAuthStore";
import * as store from "../utils/videoStore";
import { VideoPage } from "./VideoPage";

const FILE = () => new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });

async function pick() {
  const input = document.querySelector("input[type=file]") as HTMLInputElement;
  fireEvent.change(input, { target: { files: [FILE()] } });
  await waitFor(() => expect(screen.getByText("clip.mp4")).toBeTruthy());
}

async function pickAndRun() {
  await pick();
  const run = await screen.findByText("영상 처리 시작");
  await waitFor(() => expect((run.closest("button") as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(run);
}

const RESULT = { kind: "download", blob: new Blob(["mp4"]), format: "mp4", frames: 30, held: 4, effect: "blur", intensity: 22 } as const;

beforeEach(() => {
  useAuthStore.setState({ user: null, status: "guest" });
  // jsdom 에는 object URL 이 없다
  URL.createObjectURL = vi.fn(() => "blob:preview");
  URL.revokeObjectURL = vi.fn();
  vi.mocked(store.loadVideo).mockResolvedValue(null);
  vi.mocked(store.saveVideo).mockResolvedValue(true);
  vi.mocked(store.clearVideo).mockResolvedValue(true);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("VideoPage", () => {
  it("비로그인: 바로 재생 · 적용된 효과 표시 · mp4 저장 · 이 브라우저에 보관", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ ...RESULT });
    render(<VideoPage />);
    expect(screen.getByText(/아무것도 남기지 않아요/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/30프레임 처리/)).toBeTruthy();
    expect(screen.getByText(/서버에 저장되지 않았어요/)).toBeTruthy();
    expect(screen.getByTestId("video-applied").textContent).toContain("배경 블러 · 강도 22");
    const player = (await screen.findByLabelText("처리 결과 영상")) as HTMLVideoElement;
    expect(player.getAttribute("src")).toBe("blob:preview");
    expect(store.saveVideo).toHaveBeenCalledWith(
      expect.objectContaining({ owner: "guest", format: "mp4", prompt: "사람만 남기고 배경 블러", fileName: "clip.mp4", intensity: 22 }),
    );
    expect(screen.getByText("이 브라우저에 보관됨")).toBeTruthy();
    fireEvent.click(screen.getByText("결과 저장 (mp4)"));
    expect(client.saveBlob).toHaveBeenCalledWith(RESULT.blob, "clip_cutnkeep.mp4");
  });

  it("회원: 보관본을 인증 요청으로 받아 재생하고 브라우저에도 보관", async () => {
    useAuthStore.setState({ user: { id: "u1", username: "k", email: "k@x.com" } as never, status: "user" });
    const blob = new Blob(["mp4"]);
    vi.mocked(client.processVideo).mockResolvedValue({
      kind: "saved", jobId: "j1", url: "/api/v1/video/j1", format: "mp4", frames: 12, held: 0, effect: "blur", intensity: 15,
    });
    vi.mocked(client.fetchBlob).mockResolvedValue(blob);
    render(<VideoPage />);
    expect(screen.getByText(/서버에도 24시간 보관/)).toBeTruthy();
    await pickAndRun();
    expect(await screen.findByText(/서버에 보관됨/)).toBeTruthy();
    expect(client.fetchBlob).toHaveBeenCalledWith("/api/v1/video/j1");
    expect(await screen.findByLabelText("처리 결과 영상")).toBeTruthy();
    expect(store.saveVideo).toHaveBeenCalledWith(expect.objectContaining({ owner: "u1", blob }));
  });

  it("새로고침 후: 브라우저에 보관된 마지막 결과를 되살려 재생하고 문장도 채운다", async () => {
    const blob = new Blob(["mp4"]);
    vi.mocked(store.loadVideo).mockResolvedValue({
      blob, format: "mp4", frames: 9, held: 1, prompt: "배경 블러 강도 60", fileName: "trip.mov",
      effect: "blur", intensity: 60, owner: "guest", savedAt: 1,
    });
    render(<VideoPage />);
    expect(await screen.findByText("이 브라우저에 보관된 마지막 결과")).toBeTruthy();
    expect(store.loadVideo).toHaveBeenCalledWith("guest");
    expect(await screen.findByLabelText("처리 결과 영상")).toBeTruthy();
    expect((screen.getByDisplayValue("배경 블러 강도 60") as HTMLInputElement).value).toBe("배경 블러 강도 60");
    expect(screen.getByText(/원본 영상을 올려 주세요/)).toBeTruthy(); // 원본이 없으니 다시 처리는 파일을 다시 올려야
    fireEvent.click(screen.getByText("결과 저장 (mp4)"));
    expect(client.saveBlob).toHaveBeenCalledWith(blob, "trip_cutnkeep.mp4");
  });

  it("결과가 있으면 같은 영상으로 문장을 고쳐 다시 처리할 수 있다", async () => {
    vi.mocked(client.processVideo)
      .mockResolvedValueOnce({ ...RESULT, intensity: 15 })
      .mockResolvedValueOnce({ ...RESULT, intensity: 60 });
    render(<VideoPage />);
    await pickAndRun();
    await screen.findByLabelText("처리 결과 영상");
    const again = screen.getByText("다시 처리").closest("button") as HTMLButtonElement;
    expect(again.disabled).toBe(false); // 파일이 그대로 남아 있다
    fireEvent.change(screen.getByDisplayValue("사람만 남기고 배경 블러"), { target: { value: "사람만 남기고 배경 블러 강도 60" } });
    fireEvent.click(again);
    await waitFor(() => expect(client.processVideo).toHaveBeenCalledTimes(2));
    expect(vi.mocked(client.processVideo).mock.calls[1][1]).toBe("사람만 남기고 배경 블러 강도 60");
    await waitFor(() => expect(screen.getByTestId("video-applied").textContent).toContain("강도 60"));
  });

  it("문장에 블러가 있는데 다른 효과로 해석되면 알려 준다", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ ...RESULT, effect: "remove_bg", intensity: undefined });
    render(<VideoPage />);
    await pickAndRun();
    expect(await screen.findByText(/블러가 있는데 “배경 제거”로 해석됐어요/)).toBeTruthy();
  });

  it("avi 로 온 결과는 재생기 대신 내려받기 안내", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ kind: "download", blob: new Blob(["avi"]), format: "avi", frames: 3, held: 0 });
    render(<VideoPage />);
    await pickAndRun();
    expect(await screen.findByText(/ffmpeg 가 없어 avi 로/)).toBeTruthy();
    expect(screen.queryByLabelText("처리 결과 영상")).toBeNull();
    expect(screen.getByText("결과 저장 (avi)")).toBeTruthy();
  });

  it("브라우저가 재생하지 못하면 저장 안내", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ ...RESULT });
    render(<VideoPage />);
    await pickAndRun();
    fireEvent.error(await screen.findByLabelText("처리 결과 영상"));
    expect(await screen.findByText(/이 브라우저에서 재생되지 않아요/)).toBeTruthy();
    expect(screen.queryByLabelText("처리 결과 영상")).toBeNull();
  });

  it("브라우저 저장소를 못 쓰면 알려 준다", async () => {
    vi.mocked(store.saveVideo).mockResolvedValue(false);
    vi.mocked(client.processVideo).mockResolvedValue({ ...RESULT });
    render(<VideoPage />);
    await pickAndRun();
    expect(await screen.findByText(/새로고침하면 사라져요/)).toBeTruthy();
  });

  it("보관된 결과 지우기", async () => {
    vi.mocked(client.processVideo).mockResolvedValue({ ...RESULT });
    render(<VideoPage />);
    await pickAndRun();
    fireEvent.click(await screen.findByText("보관된 결과 지우기"));
    await waitFor(() => expect(screen.queryByLabelText("처리 결과 영상")).toBeNull());
    expect(store.clearVideo).toHaveBeenCalled();
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

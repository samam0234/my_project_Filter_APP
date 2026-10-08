import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/client", () => ({
  processGif: vi.fn(),
  submitFeedback: vi.fn(),
  resolveAssetUrl: (u?: string | null) => u ?? undefined,
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));

import * as client from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import { useAuthStore } from "../../store/useAuthStore";
import type { GifResponse } from "../../types";
import { GifWorkspace } from "./GifWorkspace";

const GIF = () => new File([new Uint8Array([71, 73, 70, 56, 57, 97])], "dance.gif", { type: "image/gif" });

const BASE: GifResponse = {
  job_id: "g1",
  status: "ok",
  parsed_prompt: { target: ["person"], effect: "remove_bg", intensity: 15, crop: false, selector: null },
  before_url: null,
  after_url: "data:image/gif;base64,R0lGODlh",
  frames: 12,
  total: 12,
  held: 0,
  effect: "remove_bg",
  transparent: true,
  message: null,
  saved: false,
};

async function pickAndRun() {
  const input = document.querySelector("input[type=file]") as HTMLInputElement;
  fireEvent.change(input, { target: { files: [GIF()] } });
  await waitFor(() => expect(screen.getByText("dance.gif")).toBeTruthy());
  const run = screen.getByText("GIF 처리 시작").closest("button") as HTMLButtonElement;
  await waitFor(() => expect(run.disabled).toBe(false));
  fireEvent.click(run);
}

beforeEach(() => {
  useAuthStore.setState({ user: null, status: "guest" });
  useAppStore.getState().setPrompt("사람만 남기고 배경 제거");
  URL.createObjectURL = vi.fn(() => "blob:gif-preview");
  URL.revokeObjectURL = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("GifWorkspace", () => {
  it("비로그인: 결과 GIF(data URL)와 원본 미리 보기, 저장 안 됨 안내, .gif 로 저장", async () => {
    vi.mocked(client.processGif).mockResolvedValue({ ...BASE });
    render(<GifWorkspace />);
    await pickAndRun();
    expect(await screen.findByText(/12프레임 처리 · 투명 배경/)).toBeTruthy();
    expect(client.processGif).toHaveBeenCalledWith(expect.any(File), "사람만 남기고 배경 제거");
    expect((screen.getByAltText("처리 결과") as HTMLImageElement).src).toContain("data:image/gif");
    expect((screen.getByAltText("원본 이미지") as HTMLImageElement).src).toContain("blob:gif-preview");
    expect(screen.getByText("이 결과는 저장되지 않아요")).toBeTruthy();
    expect(screen.getByRole("link", { name: /결과 저장/ }).getAttribute("download")).toBe("cutnkeep_g1.gif");
  });

  it("회원: 서버 보관본 URL · 작업 상세 링크 · 일부 프레임만 처리한 안내", async () => {
    useAuthStore.setState({ user: { id: "u", username: "m", email: "m@x" }, status: "user" });
    vi.mocked(client.processGif).mockResolvedValue({
      ...BASE,
      saved: true,
      before_url: "/api/v1/files/g1/before",
      after_url: "/api/v1/files/g1/after",
      frames: 120,
      total: 300,
      message: "프레임이 많아 앞 120개만 처리했어요 (전체 300개)",
    });
    render(<GifWorkspace />);
    await pickAndRun();
    expect(await screen.findByText(/앞 120개만 처리/)).toBeTruthy();
    expect((screen.getByAltText("원본 이미지") as HTMLImageElement).src).toContain("/api/v1/files/g1/before");
    expect(screen.getByText("작업 상세 보기").closest("a")?.getAttribute("href")).toBe("/jobs/g1");
    expect(screen.queryByText("이 결과는 저장되지 않아요")).toBeNull();
  });

  it("처리 실패는 오류로 보여 주고 다시 시도할 수 있다", async () => {
    vi.mocked(client.processGif).mockRejectedValue(new Error("GIF 형식이 아닙니다."));
    render(<GifWorkspace />);
    await pickAndRun();
    expect((await screen.findByRole("alert")).textContent).toContain("GIF 형식이 아닙니다.");
    expect((screen.getByText("GIF 처리 시작").closest("button") as HTMLButtonElement).disabled).toBe(false);
  });
});

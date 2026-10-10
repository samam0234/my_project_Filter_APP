import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchSystem: vi.fn(),
  runCleanup: vi.fn(),
  errorMessage: (e: unknown) => String((e as Error)?.message ?? e),
}));

import * as client from "../api/client";
import type { SystemSnapshot } from "../types";
import { formatBytes, SystemPage } from "./SystemPage";

const SNAP: SystemSnapshot = {
  version: "0.1.0",
  app_env: "production",
  production: true,
  segmentation: { runtime: "onnx", model_file: "yolo26m-seg.onnx", model_exists: true, prefer_onnx: true, min_confidence: 0.25 },
  mask: { exclusive: "subtract", grabcut: false, forbid_refine: false, clahe: false, hard_example_conf: 0 },
  stuff_seg: { enabled: true, model_file: "segformer-ade.onnx", model_exists: true, min_prob: 0.5, loaded: true },
  open_vocab: { enabled: true, dino_model_id: "d", sam2_model_id: "s", box_threshold: 0.35, text_threshold: 0.25, loaded: ["dino", "sam2"] },
  llm: { provider: "ollama", model: "gemma4:e4b", fallback: "ollama", chain: "langchain", votes: 3, lora_adapter: false, rag_enabled: true, rag_sources: "correction,like" },
  batch: { use_celery: true, redis_ok: false },
  video: { output_format: "webm", max_seconds: 20, max_frames: 240 },
  console: { require_login: true, admins: 2, allow_remote: false },
  storage: {
    retention_hours: 24,
    areas: [
      { name: "jobs", files: 32, bytes: 14_200_786, oldest_hours: 189.6, expired_files: 32 },
      { name: "batches", files: 0, bytes: 0, oldest_hours: null, expired_files: 0 },
      { name: "videos", files: 1, bytes: 2048, oldest_hours: 1, expired_files: 0 },
    ],
    disk: { total: 100 * 1024 ** 3, used: 95 * 1024 ** 3, free: 5 * 1024 ** 3 },
  },
  preflight: [
    { level: "warn", key: "CORS_ORIGINS", message: "localhost 만 있음" },
    { level: "error", key: "SECRET_KEY", message: "기본값" },
  ],
};

beforeEach(() => {
  vi.mocked(client.fetchSystem).mockResolvedValue(SNAP);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("SystemPage", () => {
  it("배포 점검(error 먼저)·런타임·저장 공간을 보여 준다", async () => {
    render(<SystemPage />);
    expect(await screen.findByText("SECRET_KEY")).toBeTruthy();
    const keys = screen.getAllByText(/^(SECRET_KEY|CORS_ORIGINS)$/).map((n) => n.textContent);
    expect(keys).toEqual(["SECRET_KEY", "CORS_ORIGINS"]);
    expect(screen.getByText("ONNX Runtime")).toBeTruthy();
    expect(screen.getByText("segformer-ade.onnx · 로드됨")).toBeTruthy();
    expect(screen.getByText("겹침 subtract · GrabCut 끔 · CLAHE 끔")).toBeTruthy();
    expect(screen.getByText("LangChain · 대상이 갈리면 최대 3번 다수결")).toBeTruthy();
    expect(screen.getByText(/Redis 연결 안 됨/)).toBeTruthy();
    expect(screen.getByText("dino, sam2")).toBeTruthy();
    expect(screen.getByText("13.5 MB")).toBeTruthy();
    expect(screen.getByText(/기간 지난 파일 32개/)).toBeTruthy();
  });

  it("정리는 미리 보기 후에만 실행할 수 있다", async () => {
    vi.mocked(client.runCleanup)
      .mockResolvedValueOnce({ removed_files: 32, freed_bytes: 14_200_786, removed_dirs: 0, dry_run: true, retention_hours: 24 })
      .mockResolvedValueOnce({ removed_files: 32, freed_bytes: 14_200_786, removed_dirs: 9, dry_run: false, retention_hours: 24 });
    render(<SystemPage />);
    const run = (await screen.findByText("지금 정리")).closest("button") as HTMLButtonElement;
    expect(run.disabled).toBe(true);
    fireEvent.click(screen.getByText("정리 미리 보기"));
    expect(await screen.findByText(/지울 대상: 파일 32개 · 13.5 MB/)).toBeTruthy();
    expect(client.runCleanup).toHaveBeenLastCalledWith(true);
    expect(run.disabled).toBe(false);
    fireEvent.click(run);
    expect(await screen.findByText(/정리 완료: 파일 32개 · 13.5 MB · 빈 폴더 9개/)).toBeTruthy();
    expect(client.runCleanup).toHaveBeenLastCalledWith(false);
    expect(client.fetchSystem).toHaveBeenCalledTimes(2); // 정리 후 다시 집계
  });

  it("formatBytes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(5 * 1024 ** 3)).toBe("5.0 GB");
  });
});

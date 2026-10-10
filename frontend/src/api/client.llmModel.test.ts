import { afterEach, describe, expect, it, vi } from "vitest";
import { api, processGif, processVideo, uploadImage } from "./client";

/** 요청에 실리는 폼 필드 — 작업실에서 고른 해석 모델이 서버로 가는지 (기본 모델이면 아예 안 보낸다) */
function fields(form: FormData): Record<string, string> {
  const out: Record<string, string> = {};
  form.forEach((v, k) => {
    if (typeof v === "string") out[k] = v;
  });
  return out;
}

afterEach(() => vi.restoreAllMocks());

describe("llm_model 폼 필드", () => {
  const mockPost = (response: unknown) => vi.spyOn(api, "post").mockResolvedValue(response as never);

  it("사진: 고른 모델을 llm_model 로 보내고, 안 골랐으면 필드가 없다", async () => {
    const post = mockPost({ data: {}, headers: {} });
    const file = new File(["x"], "a.jpg", { type: "image/jpeg" });
    await uploadImage(file, "사람만", "gemma4:12b");
    expect(fields(post.mock.calls[0][1] as FormData)).toEqual({ prompt: "사람만", llm_model: "gemma4:12b" });
    await uploadImage(file, "사람만");
    expect(fields(post.mock.calls[1][1] as FormData)).toEqual({ prompt: "사람만" });
    expect(post.mock.calls[0][0]).toBe("/api/v1/upload");
  });

  it("GIF: matte 와 함께 llm_model 을 보낸다", async () => {
    const post = mockPost({ data: {}, headers: {} });
    const file = new File(["x"], "a.gif", { type: "image/gif" });
    await processGif(file, "사람만", "light", "qwen3.8:27b");
    expect(fields(post.mock.calls[0][1] as FormData)).toEqual({ prompt: "사람만", matte: "light", llm_model: "qwen3.8:27b" });
    await processGif(file, "사람만", "none");
    expect(fields(post.mock.calls[1][1] as FormData)).toEqual({ prompt: "사람만", matte: "none" });
  });

  it("영상: 고른 모델을 llm_model 로 보낸다", async () => {
    const post = mockPost({ data: new Blob(["v"]), headers: { "content-type": "video/mp4", "x-cutnkeep-format": "mp4" } });
    const file = new File(["x"], "a.mp4", { type: "video/mp4" });
    await processVideo(file, "사람만", "gemma4:12b").catch(() => undefined);
    expect(fields(post.mock.calls[0][1] as FormData)).toEqual({ prompt: "사람만", llm_model: "gemma4:12b" });
    expect(post.mock.calls[0][0]).toBe("/api/v1/video");
  });

  it("사진 업로드는 큰 해석 모델을 기다릴 수 있게 5분까지 기다린다", async () => {
    const post = mockPost({ data: {}, headers: {} });
    await uploadImage(new File(["x"], "a.jpg"), "사람만");
    expect((post.mock.calls[0][2] as { timeout: number }).timeout).toBe(300_000);
  });
});

import "fake-indexeddb/auto";
import { afterEach, describe, expect, it, vi } from "vitest";
import { clearVideo, loadVideo, saveVideo, type StoredVideo } from "./videoStore";

const item = (over: Partial<StoredVideo> = {}): StoredVideo => ({
  blob: new Blob(["mp4-bytes"], { type: "video/mp4" }),
  format: "mp4",
  frames: 12,
  held: 1,
  prompt: "사람만 남기고 배경 블러",
  fileName: "clip.mp4",
  effect: "blur",
  intensity: 15,
  owner: "guest",
  savedAt: 1,
  ...over,
});

afterEach(async () => {
  await clearVideo();
  vi.unstubAllGlobals();
});

describe("videoStore (IndexedDB)", () => {
  it("저장한 결과를 다시 읽는다 (Blob · 메타 그대로)", async () => {
    expect(await saveVideo(item())).toBe(true);
    const got = await loadVideo("guest");
    expect(got?.blob).toBeTruthy(); // jsdom 은 Blob 복제 구현이 달라 크기·형식은 실제 브라우저에서 확인한다
    expect(got).toMatchObject({ format: "mp4", frames: 12, prompt: "사람만 남기고 배경 블러", effect: "blur", intensity: 15 });
  });

  it("마지막 1건만 남는다", async () => {
    await saveVideo(item({ frames: 1 }));
    await saveVideo(item({ frames: 2 }));
    expect((await loadVideo("guest"))?.frames).toBe(2);
  });

  it("다른 계정이 같은 브라우저를 써도 남의 결과는 안 보인다", async () => {
    await saveVideo(item({ owner: "user-1" }));
    expect(await loadVideo("guest")).toBeNull();
    expect(await loadVideo("user-2")).toBeNull();
    expect((await loadVideo("user-1"))?.frames).toBe(12);
  });

  it("지우면 없다", async () => {
    await saveVideo(item());
    expect(await clearVideo()).toBe(true);
    expect(await loadVideo("guest")).toBeNull();
  });

  it("IndexedDB 를 못 쓰는 환경(시크릿 창 등)에서도 예외 없이 null/false", async () => {
    vi.stubGlobal("indexedDB", undefined);
    expect(await saveVideo(item())).toBe(false);
    expect(await loadVideo("guest")).toBeNull();
    expect(await clearVideo()).toBe(false);
  });
});

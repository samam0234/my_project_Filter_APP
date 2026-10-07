import { afterEach, describe, expect, it, vi } from "vitest";
import { api, downloadFile, processVideo } from "./client";

const file = new File([new Uint8Array(4)], "v.mp4", { type: "video/mp4" });
afterEach(() => vi.restoreAllMocks());

describe("processVideo", () => {
  it("비로그인: 응답 본문이 webm, 형식·프레임 수는 헤더에서", async () => {
    const blob = new Blob(["webm"], { type: "video/webm" });
    vi.spyOn(api, "post").mockResolvedValue({
      data: blob,
      headers: { "content-type": "video/webm", "x-cutnkeep-format": "webm", "x-cutnkeep-frames": "30", "x-cutnkeep-held": "3" },
    });
    expect(await processVideo(file, "사람만")).toEqual({ kind: "download", blob, format: "webm", frames: 30, held: 3 });
  });

  it("비로그인: 서버가 avi 로 내려보낸 경우(VP8 인코더 없음)", async () => {
    const blob = new Blob(["avi"], { type: "video/x-msvideo" });
    vi.spyOn(api, "post").mockResolvedValue({
      data: blob,
      headers: { "content-type": "video/x-msvideo", "x-cutnkeep-frames": "30", "x-cutnkeep-held": "3" },
    });
    expect(await processVideo(file, "사람만")).toMatchObject({ kind: "download", format: "avi" });
  });

  it("회원: JSON 본문(job_id · url)", async () => {
    const body = { job_id: "j9", url: "/api/v1/video/j9", format: "webm", frames: 8, held: 1 };
    vi.spyOn(api, "post").mockResolvedValue({
      data: new Blob([JSON.stringify(body)], { type: "application/json" }),
      headers: { "content-type": "application/json" },
    });
    expect(await processVideo(file, "사람만")).toEqual({
      kind: "saved", jobId: "j9", url: "/api/v1/video/j9", format: "webm", frames: 8, held: 1,
    });
  });

  it("오류 본문(Blob JSON)을 풀어 errorMessage 가 detail 을 읽게 한다", async () => {
    const err = { response: { status: 400, data: new Blob([JSON.stringify({ detail: "허용 확장자: .avi" })]) } };
    vi.spyOn(api, "post").mockRejectedValue(err);
    await expect(processVideo(file, "x")).rejects.toMatchObject({ response: { data: { detail: "허용 확장자: .avi" } } });
  });
});

describe("downloadFile", () => {
  it("Blob 으로 받아 a[download] 로 저장하고 임시 주소를 해제한다", async () => {
    vi.useFakeTimers();
    vi.spyOn(api, "get").mockResolvedValue({ data: new Blob(["zip"]) });
    const create = vi.fn(() => "blob:fake");
    const revoke = vi.fn();
    Object.assign(URL, { createObjectURL: create, revokeObjectURL: revoke });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    await downloadFile("/api/v1/batch/b/download", "x.zip");
    expect(api.get).toHaveBeenCalledWith("/api/v1/batch/b/download", expect.objectContaining({ responseType: "blob" }));
    expect(click).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(10_001);
    expect(revoke).toHaveBeenCalledWith("blob:fake");
    vi.useRealTimers();
  });

  it("서버 오류(404 JSON Blob)도 detail 로 풀어서 던진다", async () => {
    const err = { response: { status: 404, data: new Blob([JSON.stringify({ detail: "받을 결과가 없습니다." })]) } };
    vi.spyOn(api, "get").mockRejectedValue(err);
    await expect(downloadFile("/x", "x.zip")).rejects.toMatchObject({ response: { data: { detail: "받을 결과가 없습니다." } } });
  });
});

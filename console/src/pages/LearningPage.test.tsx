import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchSamples: vi.fn(),
  fetchLearningStats: vi.fn(),
  reviewSample: vi.fn(),
  bulkReview: vi.fn(),
  deleteSample: vi.fn(),
  resolveAssetUrl: (u?: string | null) => u ?? undefined,
  errorMessage: (e: unknown) => String(e),
}));

import * as client from "../api/client";
import { LearningPage } from "./LearningPage";

const SAMPLE = {
  id: "s1",
  kind: "prompt",
  source: "request",
  status: "pending",
  split: null,
  origin_id: "job1",
  prompt: "맨 앞 빨간 안전모 남자 빼고 지워",
  answer: { target: ["person"], effect: "remove_bg", selector: null },
  has_image: false,
  created_at: "2026-10-06T00:00:00Z",
};

beforeEach(() => {
  vi.mocked(client.fetchSamples).mockResolvedValue({ items: [SAMPLE], total: 1, limit: 50, offset: 0 } as never);
  vi.mocked(client.fetchLearningStats).mockResolvedValue({
    by_status: { pending: 1 },
    by_source: { request: { pending: 1 } },
    approved_by_split: {},
    learning_db: "mysql",
  } as never);
  vi.mocked(client.reviewSample).mockResolvedValue({ ...SAMPLE, status: "approved" } as never);
  vi.mocked(client.deleteSample).mockResolvedValue({ id: "s1", removed_files: [] });
});

afterEach(cleanup);

describe("LearningPage (학습 데이터 검수)", () => {
  it("기본 필터는 검수 대기 문장, 목록·출처·해석 요약을 보여 준다", async () => {
    render(<LearningPage />);
    expect(await screen.findByText(SAMPLE.prompt)).toBeTruthy();
    expect(client.fetchSamples).toHaveBeenCalledWith(expect.objectContaining({ status: "pending", kind: "prompt" }));
    expect(screen.getAllByText("회원 요청").length).toBeGreaterThan(0);
    expect(screen.getByText("person · remove_bg")).toBeTruthy();
  });

  it("승인 버튼 → approve 요청 후 다시 불러오기", async () => {
    render(<LearningPage />);
    await screen.findByText(SAMPLE.prompt);
    fireEvent.click(screen.getByTitle("승인"));
    await waitFor(() => expect(client.reviewSample).toHaveBeenCalledWith("s1", "approve"));
    expect(await screen.findByText("승인했습니다.")).toBeTruthy();
    expect(client.fetchSamples).toHaveBeenCalledTimes(2);
  });

  it("정답 고쳐서 승인 — 잘못된 JSON 은 요청하지 않고 안내", async () => {
    render(<LearningPage />);
    await screen.findByText(SAMPLE.prompt);
    fireEvent.click(screen.getByTitle("정답 고쳐서 승인"));
    const editor = screen.getByDisplayValue(/"remove_bg"/);
    fireEvent.change(editor, { target: { value: "{not json" } });
    fireEvent.click(screen.getByText("고쳐서 승인"));
    expect(await screen.findByText("정답이 올바른 JSON 이 아닙니다.")).toBeTruthy();
    expect(client.reviewSample).not.toHaveBeenCalled();

    const fixed = { target: ["person"], effect: "remove_bg", selector: { position: "front", count: 1 } };
    fireEvent.change(editor, { target: { value: JSON.stringify(fixed) } });
    fireEvent.click(screen.getByText("고쳐서 승인"));
    await waitFor(() => expect(client.reviewSample).toHaveBeenCalledWith("s1", "approve", fixed, ""));
  });

  it("삭제는 확인을 받아야 한다", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValueOnce(true);
    render(<LearningPage />);
    await screen.findByText(SAMPLE.prompt);
    fireEvent.click(screen.getByTitle("삭제 (원본 파일 포함)"));
    expect(client.deleteSample).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTitle("삭제 (원본 파일 포함)"));
    await waitFor(() => expect(client.deleteSample).toHaveBeenCalledWith("s1"));
    expect(confirm).toHaveBeenCalledTimes(2);
  });
});

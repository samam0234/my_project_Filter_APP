import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ sendChat: vi.fn(), getLlmModels: vi.fn() }));
vi.mock("../api/client", async (orig) => ({ ...(await orig<typeof import("../api/client")>()), ...api }));

import { splitReply } from "../components/chat/AgentChat";
import { useAppStore } from "../store/useAppStore";
import { useChatStore } from "../store/useChatStore";
import { useLlmModelStore } from "../store/useLlmModelStore";
import { GuidePage } from "./GuidePage";

const MODELS = {
  enabled: true,
  reachable: true,
  default: "gemma4:e4b",
  models: [
    { id: "gemma4:e4b", label: "Ollama e4b", available: true, default: true, note: "" },
    { id: "gemma4:12b", label: "Ollama 12b", available: true, default: false, note: "" },
    { id: "qwen3.8:27b", label: "Qwen 3.8 · 27b", available: false, default: false, note: "" },
  ],
};

beforeEach(() => {
  api.sendChat.mockReset().mockResolvedValue({ reply: "이렇게 써 보세요.\n`강아지만 남기고 배경 블러 강도 40`", model: "gemma4:e4b", elapsed_ms: 12 });
  api.getLlmModels.mockReset().mockResolvedValue(MODELS);
  useChatStore.setState({ messages: [], sending: false, error: null, lastModel: null });
  useLlmModelStore.setState({ enabled: true, loaded: true, defaultId: "gemma4:e4b", models: MODELS.models, selected: null });
  useAppStore.setState({ prompt: "" } as never);
  window.history.replaceState(null, "", "/guide");
});
afterEach(cleanup);

describe("프롬프트 가이드 — 두 구역", () => {
  it("기본은 일반 가이드이고, 탭을 누르면 에이전트에게 묻기로 바뀌며 주소에 남는다", () => {
    render(<GuidePage />);
    expect(screen.getByRole("tab", { name: /일반 가이드/ }).getAttribute("aria-selected")).toBe("true");
    expect(screen.getByText("남기기 vs 지우기", { exact: false })).toBeTruthy(); // 기존 가이드 내용이 그대로
    expect(screen.queryByLabelText("에이전트와 채팅")).toBeNull();
    fireEvent.click(screen.getByRole("tab", { name: /에이전트에게 묻기/ }));
    expect(window.location.search).toBe("?tab=agent");
    expect(screen.getByLabelText("에이전트와 채팅")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: /일반 가이드/ }));
    expect(window.location.search).toBe("");
  });

  it("?tab=agent 로 바로 열 수 있다", () => {
    window.history.replaceState(null, "", "/guide?tab=agent");
    render(<GuidePage />);
    expect(screen.getByRole("tab", { name: /에이전트에게 묻기/ }).getAttribute("aria-selected")).toBe("true");
  });
});

describe("에이전트에게 묻기 (AI 채팅)", () => {
  beforeEach(() => window.history.replaceState(null, "", "/guide?tab=agent"));

  it("질문을 보내면 대화에 쌓이고, 추천 문장을 누르면 작업실 입력 칸에 채워 이동한다", async () => {
    render(<GuidePage />);
    fireEvent.change(screen.getByLabelText("질문 입력"), { target: { value: "배경만 흐리게?" } });
    fireEvent.click(screen.getByRole("button", { name: "보내기" }));
    await waitFor(() => expect(api.sendChat).toHaveBeenCalledTimes(1));
    expect(api.sendChat.mock.calls[0][0]).toEqual([{ role: "user", content: "배경만 흐리게?" }]);
    expect(api.sendChat.mock.calls[0][1]).toBeUndefined(); // 기본 모델이면 모델을 보내지 않는다
    await screen.findByText("강아지만 남기고 배경 블러 강도 40");
    fireEvent.click(screen.getByRole("button", { name: /작업실에서 써 보기/ }));
    expect(useAppStore.getState().prompt).toBe("강아지만 남기고 배경 블러 강도 40");
    expect(window.location.pathname).toBe("/studio");
  });

  it("고른 모델로 요청하고, 설치되지 않은 모델은 '미적용'으로 고를 수 없다", async () => {
    render(<GuidePage />);
    const select = screen.getByLabelText("AI 답변 모델") as HTMLSelectElement;
    const opts = Array.from(select.options).map((o) => [o.textContent, o.disabled]);
    expect(opts).toEqual([["Ollama e4b", false], ["Ollama 12b", false], ["Qwen 3.8 · 27b · 미적용", true]]);
    fireEvent.change(select, { target: { value: "gemma4:12b" } });
    fireEvent.click(screen.getByRole("button", { name: "배경만 흐리게 하고 싶어요" }));
    await waitFor(() => expect(api.sendChat).toHaveBeenCalled());
    expect(api.sendChat.mock.calls[0][1]).toBe("gemma4:12b");
  });

  it("이어 묻으면 이전 대화를 함께 보낸다", async () => {
    render(<GuidePage />);
    await useChatStore.getState().send("첫 질문");
    await useChatStore.getState().send("이어서");
    const second = api.sendChat.mock.calls[1][0];
    expect(second.map((m: { role: string }) => m.role)).toEqual(["user", "assistant", "user"]);
  });

  it("오류는 화면에 보여 주고 대화를 지울 수 있다", async () => {
    api.sendChat.mockRejectedValue(new Error("AI 모델에 연결하지 못했어요."));
    render(<GuidePage />);
    fireEvent.change(screen.getByLabelText("질문 입력"), { target: { value: "안녕" } });
    fireEvent.click(screen.getByRole("button", { name: "보내기" }));
    expect((await screen.findByRole("alert")).textContent).toContain("연결하지 못했어요");
    fireEvent.click(screen.getByRole("button", { name: "대화 지우기" }));
    expect(useChatStore.getState().messages).toEqual([]);
  });

  it("서버가 Ollama 해석이 아니면 채팅 대신 안내를 보여 준다", () => {
    useLlmModelStore.setState({ enabled: false, loaded: true });
    render(<GuidePage />);
    expect(screen.getByRole("status").textContent).toContain("AI 상담을 지원하지 않아요");
    expect(screen.queryByLabelText("질문 입력")).toBeNull();
  });
});

describe("splitReply", () => {
  it("백틱 문장만 추천 문장으로 나눈다", () => {
    expect(splitReply("먼저 `사람만 남기고 배경 제거` 해 보세요. 또는 `고양이 크롭`")).toEqual([
      { kind: "text", value: "먼저 " },
      { kind: "prompt", value: "사람만 남기고 배경 제거" },
      { kind: "text", value: " 해 보세요. 또는 " },
      { kind: "prompt", value: "고양이 크롭" },
    ]);
    expect(splitReply("백틱 없음")).toEqual([{ kind: "text", value: "백틱 없음" }]);
    expect(splitReply("`a`")).toEqual([{ kind: "text", value: "`a`" }]); // 한 글자는 문장이 아니다
  });
});

import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/client", () => ({
  getLlmModels: vi.fn(),
}));

import * as client from "../../api/client";
import { currentLlmModel, useLlmModelStore } from "../../store/useLlmModelStore";
import type { LlmModelList } from "../../types";
import { ModelSelect } from "./ModelSelect";

const LIST: LlmModelList = {
  enabled: true,
  reachable: true,
  default: "gemma4:e4b",
  models: [
    { id: "gemma4:e4b", label: "Ollama e4b", available: true, default: true },
    { id: "gemma4:12b", label: "Ollama 12b", available: true, default: false, note: "처음 한 번은 수십 초 걸려요." },
    { id: "qwen3.8:27b", label: "Qwen 3.8 · 27b", available: false, default: false, note: "가장 큰 모델이에요." },
  ],
};

function reset() {
  window.localStorage.clear();
  useLlmModelStore.setState({ enabled: false, loaded: false, defaultId: null, models: [], selected: null });
}

describe("ModelSelect — 처리하기 옆 해석 모델 선택", () => {
  beforeEach(() => {
    reset();
    vi.mocked(client.getLlmModels).mockReset();
  });
  afterEach(() => cleanup());

  it("설치되지 않은 모델은 '미적용'으로 보이고 고를 수 없다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValue(LIST);
    render(<ModelSelect />);
    const select = (await screen.findByLabelText("문장 해석 모델")) as HTMLSelectElement;
    const options = Array.from(select.options);
    expect(options.map((o) => o.textContent)).toEqual(["Ollama e4b", "Ollama 12b", "Qwen 3.8 · 27b · 미적용"]);
    expect(options.map((o) => o.disabled)).toEqual([false, false, true]);
    expect(select.value).toBe("gemma4:e4b"); // 기본 모델이 선택돼 있다
  });

  it("기본이 아닌 모델을 고르면 요청에 실리고, 기본으로 되돌리면 실리지 않는다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValue(LIST);
    render(<ModelSelect />);
    const select = (await screen.findByLabelText("문장 해석 모델")) as HTMLSelectElement;
    expect(currentLlmModel()).toBeUndefined();
    fireEvent.change(select, { target: { value: "gemma4:12b" } });
    expect(currentLlmModel()).toBe("gemma4:12b");
    expect(window.localStorage.getItem("cnk.llmModel")).toBe("gemma4:12b"); // 기억해 둔다
    fireEvent.change(select, { target: { value: "gemma4:e4b" } });
    expect(currentLlmModel()).toBeUndefined();
  });

  it("고른 모델의 안내(느린 모델 등)를 보여 준다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValue(LIST);
    render(<ModelSelect />);
    const select = (await screen.findByLabelText("문장 해석 모델")) as HTMLSelectElement;
    expect(screen.queryByText(/수십 초/)).toBeNull(); // 기본 모델은 안내가 없다
    fireEvent.change(select, { target: { value: "gemma4:12b" } });
    expect(await screen.findByText("처음 한 번은 수십 초 걸려요.")).toBeTruthy();
  });

  it("내려받으면 '미적용'이 사라지고 고를 수 있다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValueOnce(LIST);
    render(<ModelSelect />);
    await screen.findByText("Qwen 3.8 · 27b · 미적용");
    // 사용자가 서버에서 qwen3.8:27b 를 내려받은 뒤 창으로 돌아온다
    vi.mocked(client.getLlmModels).mockResolvedValue({
      ...LIST,
      models: LIST.models.map((m) => (m.id === "qwen3.8:27b" ? { ...m, available: true } : m)),
    });
    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });
    const opt = (await screen.findByText("Qwen 3.8 · 27b")) as HTMLOptionElement;
    expect(opt.disabled).toBe(false);
    expect(screen.queryByText(/미적용/)).toBeNull();
  });

  it("기억해 둔 모델이 그새 미적용이 되면 기본 모델로 돌아간다", async () => {
    window.localStorage.setItem("cnk.llmModel", "qwen3.8:27b");
    useLlmModelStore.setState({ selected: "qwen3.8:27b" });
    vi.mocked(client.getLlmModels).mockResolvedValue(LIST); // 27b 는 설치 안 됨
    render(<ModelSelect />);
    await waitFor(() => expect(useLlmModelStore.getState().loaded).toBe(true));
    expect(useLlmModelStore.getState().selected).toBeNull();
    expect(currentLlmModel()).toBeUndefined();
    expect(window.localStorage.getItem("cnk.llmModel")).toBeNull();
  });

  it("해석을 Ollama 가 맡지 않는 서버이거나 목록을 못 받으면 그리지 않는다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValue({ ...LIST, enabled: false });
    const { container, rerender } = render(<ModelSelect />);
    await waitFor(() => expect(useLlmModelStore.getState().loaded).toBe(true));
    expect(container.querySelector("select")).toBeNull();

    reset();
    vi.mocked(client.getLlmModels).mockRejectedValue(new Error("network"));
    rerender(<ModelSelect key="again" />);
    await waitFor(() => expect(useLlmModelStore.getState().loaded).toBe(true));
    expect(container.querySelector("select")).toBeNull();
  });

  it("처리 중에는 바꿀 수 없다", async () => {
    vi.mocked(client.getLlmModels).mockResolvedValue(LIST);
    render(<ModelSelect disabled />);
    expect(((await screen.findByLabelText("문장 해석 모델")) as HTMLSelectElement).disabled).toBe(true);
  });
});

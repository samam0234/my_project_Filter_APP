import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useAppStore } from "../../store/useAppStore";
import { PromptInput } from "./PromptInput";

afterEach(() => {
  cleanup();
  useAppStore.getState().setPrompt("");
});

describe("PromptInput", () => {
  it("입력이 store 에 반영되고 Ctrl+Enter 로만 시작", () => {
    const onSubmit = vi.fn();
    render(<PromptInput onSubmit={onSubmit} />);
    const box = screen.getByRole("textbox");
    fireEvent.change(box, { target: { value: "왼쪽 사람 지워줘" } });
    expect(useAppStore.getState().prompt).toBe("왼쪽 사람 지워줘");
    fireEvent.keyDown(box, { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
    fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("예시 칩을 누르면 프롬프트가 채워진다", () => {
    render(<PromptInput />);
    const chips = screen.getAllByRole("button");
    expect(chips.length).toBeGreaterThan(0);
    fireEvent.click(chips[0]);
    expect(useAppStore.getState().prompt).toBe(chips[0].textContent?.trim());
  });
});

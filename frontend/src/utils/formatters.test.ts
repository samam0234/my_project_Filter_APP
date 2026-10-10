import { describe, expect, it, vi } from "vitest";
import {
  classLabel,
  effectLabel,
  formatDateTime,
  formatFileSize,
  formatRelative,
  formatScore,
  statusLabel,
} from "./formatters";

describe("formatters", () => {
  it("점수·파일 크기", () => {
    expect(formatScore(0.854)).toBe("85%");
    expect(formatFileSize(512)).toBe("512 B");
    expect(formatFileSize(2048)).toBe("2.0 KB");
    expect(formatFileSize(5 * 1024 * 1024)).toBe("5.0 MB");
  });

  it("시간대 없는 백엔드 시각은 UTC 로 해석", () => {
    expect(formatDateTime("2026-10-06T00:00:00")).toBe(formatDateTime("2026-10-06T00:00:00Z"));
    expect(formatDateTime(null)).toBe("-");
    expect(formatDateTime("not-a-date")).toBe("not-a-date");
  });

  it("상대 시간", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-06T12:00:00Z"));
    expect(formatRelative("2026-10-06T11:59:30Z")).toBe("방금");
    expect(formatRelative("2026-10-06T11:50:00Z")).toBe("10분 전");
    expect(formatRelative("2026-10-06T09:00:00")).toBe("3시간 전");
    expect(formatRelative("2026-10-04T12:00:00Z")).toBe("2일 전");
    vi.useRealTimers();
  });

  it("라벨 — 모르는 값은 그대로", () => {
    expect(effectLabel("remove_object")).toBe("대상 지우기");
    expect(effectLabel("teleport")).toBe("teleport");
    expect(classLabel("cell phone")).toBe("휴대폰");
    expect(classLabel("building")).toBe("건물");
    expect(classLabel("sky")).toBe("하늘");
    expect(classLabel("unknown-thing")).toBe("unknown-thing");
    expect(classLabel("zebra")).toBe("zebra");
    expect(statusLabel("fallback")).toBe("부분 성공");
  });
});

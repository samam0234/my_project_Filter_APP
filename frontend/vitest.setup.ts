/** jsdom 에 없는 브라우저 API 대체 (테스트 전용). */
import { vi } from "vitest";

window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;

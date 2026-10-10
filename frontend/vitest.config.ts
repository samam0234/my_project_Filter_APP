/**
 * 단위·컴포넌트 테스트 (vitest + Testing Library, jsdom).
 * 테스트 파일(*.test.ts[x])은 tsconfig.app.json 에서 빼 프로덕션 빌드(tsc -b)와 분리한다.
 */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});

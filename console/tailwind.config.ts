/**
 * 운영 콘솔 Tailwind 설정.
 * console.* 색상 토큰 (다크 ops UI).
 */
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        console: {
          bg: "#0b1220",
          panel: "#111827",
          border: "#1f2937",
          accent: "#22d3ee",
          muted: "#94a3b8",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;

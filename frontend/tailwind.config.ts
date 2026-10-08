/**
 * 사용자 앱 Tailwind 설정.
 * brand 색상 스케일 · 한국어 글꼴(Pretendard) · 그림자/애니메이션 토큰.
 */
import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Pretendard 는 main.tsx 에서 동적 서브셋 CSS 로 불러온다 (한글 글리프를 쓰는 만큼만 받음)
        sans: ['"Pretendard Variable"', "Pretendard", ...defaultTheme.fontFamily.sans],
      },
      colors: {
        // 컷앤킵 브랜드 (하늘색 계열)
        brand: {
          50: "#eef9ff",
          100: "#d9f1ff",
          200: "#bce7ff",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgb(14 165 233 / 0.25), 0 8px 32px -8px rgb(14 165 233 / 0.35)",
        card: "inset 0 1px 0 0 rgb(255 255 255 / 0.04), 0 1px 2px 0 rgb(0 0 0 / 0.4)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s ease-out both",
      },
    },
  },
  plugins: [],
} satisfies Config;

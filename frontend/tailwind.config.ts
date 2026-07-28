/**
 * 사용자 앱 Tailwind 설정.
 * brand 색상 스케일을 디자인 토큰으로 확장.
 */
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // 컷앤킵 브랜드 (하늘색 계열)
        brand: {
          50: "#eef9ff",
          100: "#d9f1ff",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;

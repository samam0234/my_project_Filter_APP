/**
 * 운영 콘솔 Vite 설정.
 * - dev 서버 포트 5174 (사용자 앱 5173 과 분리)
 * - /api, /health → 백엔드(8000) 프록시
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

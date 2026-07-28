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
    // 【수동】 운영 콘솔 dev 포트
    port: 5174,
    // 【수동】 백엔드 target — CORS 에 5174 도 포함되어 있어야 함 (CORS_ORIGINS)
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

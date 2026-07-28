/**
 * 사용자 앱 Vite 설정.
 * - dev 서버 포트 5173
 * - /api, /health → 백엔드(8000) 프록시 (CORS 없이 동일 오리진처럼 호출)
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
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

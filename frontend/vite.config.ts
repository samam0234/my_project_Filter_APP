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
    // 【수동】 사용자 앱 dev 포트 — 콘솔(5174)과 겹치지 말 것
    port: 5173,
    // 【수동】 백엔드 주소 — 포트/호스트 바뀌면 target 수정
    // 기능: 브라우저 동일 오리진처럼 /api, /health 를 FastAPI 로 넘김
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

/// <reference types="vite/client" />

/**
 * Vite 환경변수 타입 (콘솔).
 * VITE_API_BASE_URL 미설정 시 vite proxy 로 백엔드 연결.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

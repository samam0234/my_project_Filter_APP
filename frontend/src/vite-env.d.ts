/// <reference types="vite/client" />

/**
 * Vite 환경변수 타입.
 * VITE_API_BASE_URL 이 비어 있으면 동일 오리진 + vite proxy 사용.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

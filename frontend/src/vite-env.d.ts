/// <reference types="vite/client" />

/**
 * Vite 환경변수 타입.
 * VITE_API_BASE_URL 이 비어 있으면 동일 오리진 + vite proxy 사용.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  /** 개인정보 처리방침 · 약관의 운영자 정보 (src/data/legal.ts) */
  readonly VITE_OPERATOR_NAME?: string;
  readonly VITE_OPERATOR_EMAIL?: string;
  readonly VITE_POLICY_DATE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

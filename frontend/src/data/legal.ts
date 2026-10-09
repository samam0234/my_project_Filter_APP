/**
 * 개인정보 처리방침 · 이용약관에 들어가는 운영자 정보.
 *
 * 【배포 필수】 빌드 전에 .env(frontend) 또는 Docker 빌드 인자로 설정한다:
 *   VITE_OPERATOR_NAME   — 운영자(사업자) 이름
 *   VITE_OPERATOR_EMAIL  — 개인정보 문의 · 계정 삭제 요청 받을 주소
 *   VITE_POLICY_DATE     — 시행일 (YYYY-MM-DD)
 * 비어 있으면 화면에 "설정 필요"가 보인다 — 공개 전에 반드시 채운다 (docs/guidance/legal.md).
 *
 * 보관 기간 · 수집 항목은 실제 동작(백엔드 설정 기본값)과 같아야 한다. 설정을 바꾸면 여기와 문서도 함께 고친다.
 */

export const OPERATOR = {
  name: import.meta.env.VITE_OPERATOR_NAME || "(운영자 이름 — 설정 필요)",
  email: import.meta.env.VITE_OPERATOR_EMAIL || "(문의 메일 — 설정 필요)",
  policyDate: import.meta.env.VITE_POLICY_DATE || "2026-10-09",
};

// 백엔드 기본값과 같게 유지 (FILE_RETENTION_HOURS · LOG_RETENTION_DAYS · DB_BACKUP_KEEP · DB_BACKUP_HOURS)
// feedbackImageDays 는 백엔드 FEEDBACK_IMAGE_RETENTION_DAYS — Docker 는 같은 값을 빌드 인자로 넣는다
export const RETENTION = {
  fileHours: 24,
  logDays: 14,
  backupDays: 7,
  feedbackImageDays: Number(import.meta.env.VITE_FEEDBACK_IMAGE_DAYS || 30),
};

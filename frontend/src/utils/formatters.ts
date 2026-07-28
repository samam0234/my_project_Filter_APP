/**
 * UI 표시용 포맷 헬퍼 (순수 함수).
 */

/** 0~1 quality_score → "85%" 형태 */
export function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/** 바이트 수를 B / KB / MB 문자열로 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

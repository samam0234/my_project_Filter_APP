/**
 * UI 표시용 포맷 헬퍼 (순수 함수).
 */
import type { Effect, Position } from "../types";

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

/** 백엔드 created_at(UTC, 시간대 표기 없음) → 로컬 "2026. 9. 30. 오전 3:59" */
export function formatDateTime(iso?: string | null): string {
  if (!iso) return "-";
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  const d = new Date(hasZone ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("ko-KR", { dateStyle: "medium", timeStyle: "short" });
}

/** "3분 전" 같은 상대 시간 (1주 넘으면 날짜) */
export function formatRelative(iso?: string | null): string {
  if (!iso) return "-";
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  const d = new Date(hasZone ? iso : `${iso}Z`);
  const sec = Math.round((Date.now() - d.getTime()) / 1000);
  if (Number.isNaN(sec)) return iso;
  if (sec < 60) return "방금";
  if (sec < 3600) return `${Math.floor(sec / 60)}분 전`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}시간 전`;
  if (sec < 604800) return `${Math.floor(sec / 86400)}일 전`;
  return formatDateTime(iso);
}

export const EFFECT_LABELS: Record<Effect, string> = {
  remove_bg: "배경 제거",
  blur: "배경 블러",
  crop: "크롭",
  none: "효과 없음",
  remove_object: "대상 지우기",
};

export const POSITION_LABELS: Record<Position, string> = {
  front: "맨 앞",
  back: "맨 뒤",
  left: "왼쪽",
  right: "오른쪽",
  center: "가운데",
  largest: "가장 큰",
  smallest: "가장 작은",
};

/** 자주 쓰는 COCO 클래스 한국어 표기 (없으면 영어 그대로) */
const CLASS_LABELS: Record<string, string> = {
  person: "사람",
  dog: "개",
  cat: "고양이",
  car: "자동차",
  bus: "버스",
  truck: "트럭",
  bicycle: "자전거",
  motorcycle: "오토바이",
  bird: "새",
  horse: "말",
  cup: "컵",
  bottle: "병",
  chair: "의자",
  laptop: "노트북",
  "cell phone": "휴대폰",
  handbag: "가방",
  backpack: "배낭",
  bag: "가방",
};

export function effectLabel(effect?: string | null): string {
  return EFFECT_LABELS[(effect ?? "") as Effect] ?? effect ?? "-";
}

export function positionLabel(position?: string | null): string {
  return POSITION_LABELS[(position ?? "") as Position] ?? position ?? "";
}

export function classLabel(name: string): string {
  return CLASS_LABELS[name] ?? name;
}

/** 작업 상태 → 한국어 */
export function statusLabel(status: string): string {
  return (
    { ok: "완료", fallback: "부분 성공", failed: "실패", pending: "대기" } as Record<string, string>
  )[status] ?? status;
}

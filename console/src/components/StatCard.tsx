/**
 * 대시보드 요약 카드.
 * tone 에 따라 값 텍스트 색을 바꾼다 (ok/warn/bad).
 */
import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "ok" | "warn" | "bad";
}) {
  // 상태에 따른 강조 색
  const toneClass =
    tone === "ok"
      ? "text-emerald-400"
      : tone === "warn"
        ? "text-amber-400"
        : tone === "bad"
          ? "text-rose-400"
          : "text-white";

  return (
    <div className="rounded-xl border border-console-border bg-console-panel p-4">
      <p className="text-xs uppercase tracking-wide text-console-muted">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-console-muted">{hint}</p>}
    </div>
  );
}

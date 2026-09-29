/**
 * 작업 상태 배지 (ok / fallback / failed / pending).
 */
import { statusLabel } from "../../utils/formatters";

const tones: Record<string, string> = {
  ok: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  fallback: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  failed: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
  pending: "bg-slate-500/15 text-slate-300 ring-slate-500/30",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
        tones[status] ?? tones.pending
      }`}
    >
      {statusLabel(status)}
    </span>
  );
}

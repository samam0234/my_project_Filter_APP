import { Loader2 } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

export function ProcessingStatus() {
  const isProcessing = useAppStore((s) => s.isProcessing);
  const error = useAppStore((s) => s.error);

  if (!isProcessing && !error) return null;

  return (
    <div className="space-y-2">
      {isProcessing && (
        <div className="flex items-center gap-2 rounded-xl border border-brand-700/40 bg-brand-900/20 px-3 py-2 text-sm text-brand-100">
          <Loader2 className="h-4 w-4 animate-spin" />
          처리 중… (세그멘테이션 · 마스크 · 효과)
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}
    </div>
  );
}

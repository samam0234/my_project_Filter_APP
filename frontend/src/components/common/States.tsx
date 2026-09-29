/**
 * 로딩 · 에러 · 빈 상태 공통 블록.
 */
import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { Button } from "./Button";

export function LoadingBlock({ label = "불러오는 중…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/40 py-12 text-sm text-slate-400">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-rose-900/50 bg-rose-950/30 py-10 text-center text-sm text-rose-200">
      <AlertTriangle className="h-5 w-5" />
      <p>{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          다시 시도
        </Button>
      )}
    </div>
  );
}

export function EmptyBlock({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-slate-800 py-12 text-center text-sm text-slate-400">
      <Inbox className="h-6 w-6 text-slate-500" />
      <p className="font-medium text-slate-300">{title}</p>
      {children}
    </div>
  );
}

/**
 * 로딩 · 에러 · 빈 상태 공통 블록.
 */
import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { Button } from "./Button";

export function LoadingBlock({ label = "불러오는 중…" }: { label?: string }) {
  return (
    <div className="card flex items-center justify-center gap-2 py-12 text-sm text-slate-400" role="status">
      <Loader2 className="h-4 w-4 animate-spin text-brand-400" /> {label}
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      className="flex flex-col items-center gap-3 rounded-2xl border border-rose-900/50 bg-rose-950/25 px-6 py-10 text-center text-sm text-rose-200"
      role="alert"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-500/10 ring-1 ring-inset ring-rose-500/30">
        <AlertTriangle className="h-5 w-5" />
      </span>
      <p>{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          다시 시도
        </Button>
      )}
    </div>
  );
}

export function EmptyBlock({
  title,
  children,
  icon: Icon = Inbox,
}: {
  title: string;
  children?: ReactNode;
  icon?: typeof Inbox;
}) {
  return (
    <div className="flex flex-col items-center gap-2.5 rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 px-6 py-12 text-center text-sm text-slate-400">
      <span className="mb-1 flex h-11 w-11 items-center justify-center rounded-full bg-slate-800/70 ring-1 ring-inset ring-slate-700/60">
        <Icon className="h-5 w-5 text-slate-400" />
      </span>
      <p className="font-medium text-slate-200">{title}</p>
      {children}
    </div>
  );
}

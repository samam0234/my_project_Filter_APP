/**
 * 좌측 네비게이션.
 * useConsoleStore.page 를 바꿔 본문 페이지 전환.
 * 하단: API online/offline · DB dialect 요약.
 */
import {
  Activity,
  ExternalLink,
  LayoutDashboard,
  ListOrdered,
  Server,
} from "lucide-react";
import type { ConsolePage } from "../types";
import { useConsoleStore } from "../store/useConsoleStore";

const items: { id: ConsolePage; label: string; icon: typeof Activity }[] = [
  { id: "dashboard", label: "대시보드", icon: LayoutDashboard },
  { id: "jobs", label: "Job 목록", icon: ListOrdered },
  { id: "system", label: "시스템", icon: Server },
  { id: "links", label: "바로가기", icon: ExternalLink },
];

export function Sidebar() {
  const page = useConsoleStore((s) => s.page);
  const setPage = useConsoleStore((s) => s.setPage);
  const health = useConsoleStore((s) => s.health);

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-console-border bg-console-panel">
      <div className="border-b border-console-border px-4 py-5">
        <div className="flex items-center gap-2 text-console-accent">
          <Activity className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-widest">
            Ops Console
          </span>
        </div>
        <p className="mt-2 text-sm font-semibold text-white">Cut & Keep</p>
        <p className="text-xs text-console-muted">운영 · 모니터링 관리자</p>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        {items.map(({ id, label, icon: Icon }) => {
          const active = page === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setPage(id)}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition ${
                active
                  ? "bg-cyan-500/15 text-console-accent"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          );
        })}
      </nav>

      {/* 연결 상태 요약 (health 스냅샷) */}
      <div className="border-t border-console-border p-4 text-xs text-console-muted">
        <div className="flex items-center justify-between">
          <span>API</span>
          <span
            className={
              health?.status === "ok" ? "text-emerald-400" : "text-rose-400"
            }
          >
            {health?.status === "ok" ? "online" : "offline"}
          </span>
        </div>
        <div className="mt-1 flex items-center justify-between">
          <span>DB</span>
          <span className="text-slate-300">{health?.db_dialect || "-"}</span>
        </div>
      </div>
    </aside>
  );
}

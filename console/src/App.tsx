import { useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { useConsoleData } from "./hooks/useConsoleData";
import { useConsoleStore } from "./store/useConsoleStore";
import { DashboardPage } from "./pages/DashboardPage";
import { JobsPage } from "./pages/JobsPage";
import { LinksPage } from "./pages/LinksPage";
import { SystemPage } from "./pages/SystemPage";

export default function App() {
  const page = useConsoleStore((s) => s.page);
  const error = useConsoleStore((s) => s.error);
  const { refresh, loading } = useConsoleData();

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-console-border bg-console-panel/80 px-6 py-3 backdrop-blur">
          <div>
            <p className="text-xs uppercase tracking-widest text-console-muted">
              Administration
            </p>
            <h1 className="text-lg font-semibold text-white">운영 콘솔</h1>
          </div>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-console-border bg-slate-900 px-3 py-2 text-sm text-slate-100 transition hover:border-console-accent disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            새로고침
          </button>
        </header>

        <main className="flex-1 overflow-auto p-6">
          {error && page !== "system" && (
            <div className="mb-4 rounded-xl border border-amber-800/40 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
              {error}
            </div>
          )}
          {page === "dashboard" && <DashboardPage />}
          {page === "jobs" && <JobsPage />}
          {page === "system" && <SystemPage />}
          {page === "links" && <LinksPage />}
        </main>
      </div>
    </div>
  );
}

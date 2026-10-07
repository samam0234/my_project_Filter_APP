/**
 * 운영 콘솔 루트 (Vite :5174).
 *
 * - 좌측 Sidebar 로 페이지 전환 (dashboard / jobs / batches / users / learning / system / links)
 * - 먼저 /console/me 로 접근 확인 → 401·403 이면 로그인 화면 (관리자 계정 · 서버 PC 는 바로 통과)
 * - 들어온 뒤 마운트 시 + 30초 간격으로 health·jobs 새로고침
 * - useConsoleStore.page 에 따라 해당 Page 컴포넌트 렌더
 */
import { useEffect } from "react";
import { LogOut, RefreshCw } from "lucide-react";
import { consoleLogout, errorMessage, fetchConsoleMe, setAuthRequiredHandler } from "./api/client";
import { Sidebar } from "./components/Sidebar";
import { useConsoleData } from "./hooks/useConsoleData";
import { useConsoleStore } from "./store/useConsoleStore";
import { DashboardPage } from "./pages/DashboardPage";
import { JobsPage } from "./pages/JobsPage";
import { BatchesPage } from "./pages/BatchesPage";
import { UsersPage } from "./pages/UsersPage";
import { LearningPage } from "./pages/LearningPage";
import { LinksPage } from "./pages/LinksPage";
import { LoginPage } from "./pages/LoginPage";
import { SystemPage } from "./pages/SystemPage";

export default function App() {
  const page = useConsoleStore((s) => s.page);
  const error = useConsoleStore((s) => s.error);
  const auth = useConsoleStore((s) => s.auth);
  const me = useConsoleStore((s) => s.me);
  const signedIn = useConsoleStore((s) => s.signedIn);
  const requireLogin = useConsoleStore((s) => s.requireLogin);
  const { refresh, loading } = useConsoleData();

  // 접근 확인 + 이후 어느 요청이든 401·403 이면 로그인 화면으로 (세션 만료 등)
  useEffect(() => {
    setAuthRequiredHandler((message) => requireLogin(message));
    fetchConsoleMe()
      .then(signedIn)
      .catch((err) => requireLogin(err?.response ? null : errorMessage(err)));
    return () => setAuthRequiredHandler(null);
  }, [requireLogin, signedIn]);

  // 들어온 뒤 최초 로드 + 30초 폴링 (운영 모니터링용)
  useEffect(() => {
    if (auth !== "in") return;
    void refresh();
    const t = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(t);
  }, [auth, refresh]);

  const logout = async () => {
    await consoleLogout().catch(() => undefined);
    requireLogin(null);
  };

  if (auth === "checking") {
    return <p className="p-6 text-sm text-console-muted">콘솔 접근 확인 중…</p>;
  }
  if (auth === "login") return <LoginPage />;

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
          <div className="flex items-center gap-3">
            <span className="text-xs text-console-muted" data-testid="console-actor">
              {me?.via === "admin"
                ? `관리자 ${me.username}`
                : me?.via === "local"
                  ? "서버 PC (로그인 없음)"
                  : "원격 허용 (CONSOLE_ALLOW_REMOTE)"}
            </span>
            {me?.via === "admin" && (
              <button
                type="button"
                onClick={() => void logout()}
                className="inline-flex items-center gap-1 rounded-lg border border-console-border px-2 py-2 text-xs text-slate-300 transition hover:border-console-accent"
              >
                <LogOut className="h-4 w-4" /> 로그아웃
              </button>
            )}
            <button
              type="button"
              onClick={() => void refresh()}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-console-border bg-slate-900 px-3 py-2 text-sm text-slate-100 transition hover:border-console-accent disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              새로고침
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          {/* system 페이지는 자체 에러 표시가 있어 상단 배너 생략 */}
          {error && page !== "system" && (
            <div className="mb-4 rounded-xl border border-amber-800/40 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
              {error}
            </div>
          )}
          {page === "dashboard" && <DashboardPage />}
          {page === "jobs" && <JobsPage />}
          {page === "batches" && <BatchesPage />}
          {page === "users" && <UsersPage />}
          {page === "learning" && <LearningPage />}
          {page === "system" && <SystemPage />}
          {page === "links" && <LinksPage />}
        </main>
      </div>
    </div>
  );
}

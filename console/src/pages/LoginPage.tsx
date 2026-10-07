/**
 * 운영 콘솔 로그인.
 *
 * 사용자 앱과 같은 계정·로그인 API 를 쓰고, 서버 설정 CONSOLE_ADMINS 에 있는 아이디만 들어갈 수 있다.
 * 로그인은 됐지만 관리자가 아니면 세션을 바로 끊는다 (콘솔 도메인에 일반 회원 세션을 남기지 않게).
 */
import { useState, type FormEvent } from "react";
import { Lock } from "lucide-react";
import { consoleLogin, consoleLogout, errorMessage, fetchConsoleMe } from "../api/client";
import { useConsoleStore } from "../store/useConsoleStore";

export function LoginPage() {
  const authMessage = useConsoleStore((s) => s.authMessage);
  const signedIn = useConsoleStore((s) => s.signedIn);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await consoleLogin(username.trim(), password);
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
      return;
    }
    try {
      signedIn(await fetchConsoleMe());
    } catch (err) {
      setError(errorMessage(err));
      await consoleLogout().catch(() => undefined);
    } finally {
      setBusy(false);
      setPassword("");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={(e) => void submit(e)}
        className="w-full max-w-sm space-y-4 rounded-2xl border border-console-border bg-console-panel p-6"
      >
        <div className="flex items-center gap-2 text-console-accent">
          <Lock className="h-5 w-5" />
          <span className="text-xs font-bold uppercase tracking-widest">Ops Console</span>
        </div>
        <div>
          <h1 className="text-lg font-semibold text-white">관리자 로그인</h1>
          <p className="mt-1 text-xs text-console-muted">
            컷앤킵 계정 중 서버에 관리자로 등록된 아이디(CONSOLE_ADMINS)만 들어올 수 있어요.
          </p>
        </div>
        {(error || authMessage) && (
          <p role="alert" className="rounded-lg border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
            {error || authMessage}
          </p>
        )}
        <label className="block space-y-1 text-sm">
          <span className="text-slate-300">아이디</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            className="w-full rounded-lg border border-console-border bg-slate-900 px-3 py-2 text-slate-100 outline-none focus:border-console-accent"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="text-slate-300">비밀번호</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            className="w-full rounded-lg border border-console-border bg-slate-900 px-3 py-2 text-slate-100 outline-none focus:border-console-accent"
          />
        </label>
        <button
          type="submit"
          disabled={busy || !username.trim() || !password}
          className="w-full rounded-lg bg-cyan-500/20 px-3 py-2 text-sm font-medium text-console-accent transition hover:bg-cyan-500/30 disabled:opacity-50"
        >
          {busy ? "확인 중…" : "로그인"}
        </button>
      </form>
    </div>
  );
}

/**
 * 사용자 앱 공통 레이아웃 — 상단 내비게이션 · 서버 상태 · 푸터.
 *
 * 메뉴: 홈 / 작업실 / 작업 기록 / 프롬프트 가이드 / 배치
 * (작업 상세 /jobs/:id 는 작업 기록에서 들어가므로 메뉴에서는 "작업 기록" 을 활성으로 표시)
 */
import type { ReactNode } from "react";
import { useState } from "react";
import { BookOpen, History, Home, Layers, Lock, LogIn, LogOut, Scissors, UserRound, Wand2 } from "lucide-react";
import { Link, navigate, usePathname } from "../../router";
import { useHealth } from "../../hooks/useApi";
import { useAppStore } from "../../store/useAppStore";
import { displayName, useAuthStore } from "../../store/useAuthStore";

// members: 로그인 회원 전용 메뉴 (비로그인에게는 자물쇠 표시, 누르면 로그인 안내)
const NAV = [
  { to: "/", label: "홈", icon: Home, match: (p: string) => p === "/", members: false },
  { to: "/studio", label: "작업실", icon: Wand2, match: (p: string) => p.startsWith("/studio"), members: false },
  {
    to: "/history",
    label: "작업 기록",
    icon: History,
    match: (p: string) => p.startsWith("/history") || p.startsWith("/jobs"),
    members: true,
  },
  { to: "/guide", label: "프롬프트 가이드", icon: BookOpen, match: (p: string) => p.startsWith("/guide"), members: false },
  { to: "/batch", label: "배치", icon: Layers, match: (p: string) => p.startsWith("/batch"), members: true },
];

function ServerStatus() {
  const { online, health } = useHealth();
  const tone = online === null ? "bg-slate-500" : online ? "bg-emerald-400" : "bg-rose-500";
  const label = online === null ? "확인 중" : online ? "서버 연결됨" : "서버 연결 안 됨";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 px-2.5 py-1 text-xs text-slate-400"
      title={health ? `v${health.version} · phase ${health.phase} · ${health.db_dialect ?? ""}` : undefined}
    >
      <span className={`h-2 w-2 rounded-full ${tone}`} />
      <span className="hidden sm:inline">{label}</span>
    </span>
  );
}

/** 헤더 우측 계정 영역 — 비로그인: 로그인·회원가입 / 로그인: 이름(내 작업) · 로그아웃 */
function AccountMenu() {
  const pathname = usePathname();
  const { user, status, logout } = useAuthStore();
  const [busy, setBusy] = useState(false);

  if (status === "loading") return <span className="h-8 w-16 animate-pulse rounded-lg bg-slate-900" />;

  if (!user) {
    const onAuthPage = ["/login", "/signup", "/find-id", "/find-password"].includes(pathname);
    const next = onAuthPage ? "" : "?next=" + encodeURIComponent(pathname);
    return (
      <div className="flex shrink-0 items-center gap-1">
        <Link
          to={"/login" + next}
          className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-900 hover:text-white"
        >
          <LogIn className="h-4 w-4" />
          <span className="hidden sm:inline">로그인</span>
        </Link>
        <Link
          to="/signup"
          className="hidden rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-500 sm:inline-flex"
        >
          회원가입
        </Link>
      </div>
    );
  }

  return (
    <div className="flex shrink-0 items-center gap-1">
      <Link
        to="/history"
        title={user.username + " · " + user.email + " — 내 작업 보기"}
        className="inline-flex max-w-[10rem] items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-200 hover:bg-slate-900"
      >
        <UserRound className="h-4 w-4 shrink-0 text-brand-500" />
        <span className="hidden truncate sm:inline">{displayName(user)}</span>
      </Link>
      <button
        type="button"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          await logout();
          // 로그인 상태에서 만든 결과(피드백·상세 링크)는 비로그인에서 쓸 수 없으므로 비운다
          useAppStore.getState().setResult(null);
          setBusy(false);
          navigate("/");
        }}
        aria-label="로그아웃"
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-400 hover:bg-slate-900 hover:text-white"
      >
        <LogOut className="h-4 w-4" />
        <span className="hidden md:inline">로그아웃</span>
      </button>
    </div>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const guest = useAuthStore((s) => s.status === "guest");
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <Link to="/" className="flex shrink-0 items-center gap-2 text-white">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <Scissors className="h-4 w-4" />
            </span>
            <span className="font-semibold">컷앤킵</span>
          </Link>
          <nav className="-mx-1 flex min-w-0 flex-1 gap-1 overflow-x-auto px-1">
            {NAV.map(({ to, label, icon: Icon, match, members }) => {
              const active = match(pathname);
              const locked = members && guest;
              return (
                <Link
                  key={to}
                  to={to}
                  aria-current={active ? "page" : undefined}
                  className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition ${
                    active
                      ? "bg-slate-800 text-white"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden md:inline">{label}</span>
                  {locked && <Lock className="h-3 w-3 text-slate-600" aria-label="로그인 필요" />}
                </Link>
              );
            })}
          </nav>
          <ServerStatus />
          <AccountMenu />
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>

      <footer className="border-t border-slate-800/80">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-slate-500">
          <span>Cut &amp; Keep · 프롬프트로 원하는 것만 남기기</span>
          <span>YOLO26m-seg · LangGraph · OpenCV · Ollama / LoRA</span>
        </div>
      </footer>
    </div>
  );
}

/**
 * 사용자 앱 공통 레이아웃 — 상단 내비게이션 · 서버 상태 · 푸터.
 *
 * 메뉴: 홈 / 작업실 / 작업 기록 / 프롬프트 가이드 / 배치 / 영상
 * (작업 상세 /jobs/:id 는 작업 기록에서 들어가므로 메뉴에서는 "작업 기록" 을 활성으로 표시)
 * lg 미만에서는 메뉴를 이름이 보이는 펼침 목록(햄버거)으로 바꾼다 — 아이콘만 늘어놓으면 무엇인지 모른다.
 */
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Clapperboard,
  History,
  Home,
  Layers,
  Lock,
  LogIn,
  LogOut,
  Menu,
  Scissors,
  UserRound,
  Wand2,
  X,
} from "lucide-react";
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
  { to: "/video", label: "영상", icon: Clapperboard, match: (p: string) => p.startsWith("/video"), members: false },
];

function ServerStatus() {
  const { online, health } = useHealth();
  const tone = online === null ? "bg-slate-500" : online ? "bg-emerald-400" : "bg-rose-500";
  const label = online === null ? "확인 중" : online ? "서버 연결됨" : "서버 연결 안 됨";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-2.5 py-1 text-xs text-slate-400"
      title={health ? `v${health.version} · phase ${health.phase} · ${health.db_dialect ?? ""}` : label}
      aria-label={label}
    >
      <span className="relative flex h-2 w-2">
        {online && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />}
        <span className={`relative inline-flex h-2 w-2 rounded-full ${tone}`} />
      </span>
      <span className="hidden xl:inline">{label}</span>
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
          className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-900 hover:text-white"
        >
          <LogIn className="h-4 w-4" />
          <span className="hidden sm:inline">로그인</span>
        </Link>
        <Link
          to="/signup"
          className="hidden rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white shadow-glow transition hover:bg-brand-500 sm:inline-flex"
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
        className="inline-flex max-w-[10rem] items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-slate-200 transition hover:bg-slate-900"
      >
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500/15 ring-1 ring-inset ring-brand-500/30">
          <UserRound className="h-3.5 w-3.5 text-brand-300" />
        </span>
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
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-400 transition hover:bg-slate-900 hover:text-white"
      >
        <LogOut className="h-4 w-4" />
        <span className="hidden lg:inline">로그아웃</span>
      </button>
    </div>
  );
}

function NavLinks({ pathname, guest, vertical = false }: { pathname: string; guest: boolean; vertical?: boolean }) {
  return (
    <>
      {NAV.map(({ to, label, icon: Icon, match, members }) => {
        const active = match(pathname);
        const locked = members && guest;
        return (
          <Link
            key={to}
            to={to}
            aria-current={active ? "page" : undefined}
            className={`inline-flex shrink-0 items-center gap-2 rounded-lg text-sm transition ${
              vertical ? "w-full px-3 py-2.5" : "px-3 py-1.5"
            } ${
              active
                ? "bg-slate-800/80 text-white shadow-card"
                : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
            }`}
          >
            <Icon className={`h-4 w-4 ${active ? "text-brand-400" : ""}`} />
            <span>{label}</span>
            {locked && <Lock className="ml-auto h-3 w-3 text-slate-600" aria-label="로그인 필요" />}
          </Link>
        );
      })}
    </>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const guest = useAuthStore((s) => s.status === "guest");
  const [menuOpen, setMenuOpen] = useState(false);

  // 페이지를 옮기면 펼친 메뉴를 닫는다
  useEffect(() => setMenuOpen(false), [pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-slate-800/70 bg-slate-950/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <Link to="/" className="flex shrink-0 items-center gap-2 text-white">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 shadow-glow">
              <Scissors className="h-4 w-4" />
            </span>
            <span className="text-[15px] font-bold tracking-tight">컷앤킵</span>
          </Link>
          <nav aria-label="주 메뉴" className="hidden min-w-0 flex-1 items-center gap-0.5 lg:flex">
            <NavLinks pathname={pathname} guest={guest} />
          </nav>
          <span className="flex-1 lg:hidden" />
          <ServerStatus />
          <AccountMenu />
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            aria-label={menuOpen ? "메뉴 닫기" : "메뉴 열기"}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-300 transition hover:bg-slate-900 hover:text-white lg:hidden"
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {menuOpen && (
          <nav
            id="mobile-menu"
            aria-label="주 메뉴"
            className="animate-fade-up border-t border-slate-800/70 px-4 pb-4 pt-2 lg:hidden"
          >
            <div className="grid gap-1">
              <NavLinks pathname={pathname} guest={guest} vertical />
            </div>
          </nav>
        )}
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 animate-fade-up px-4 py-8 sm:py-10" key={pathname}>
        {children}
      </main>

      <footer className="border-t border-slate-800/70">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-slate-500">
          <span className="flex items-center gap-2">
            <Scissors className="h-3.5 w-3.5 text-slate-600" />
            컷앤킵 · 말로 하면, 원하는 것만 남깁니다
          </span>
          <span className="flex flex-wrap gap-x-4 gap-y-1">
            <Link to="/guide" className="hover:text-slate-300">
              프롬프트 가이드
            </Link>
            <Link to="/studio" className="hover:text-slate-300">
              작업실
            </Link>
            <Link to="/video" className="hover:text-slate-300">
              영상
            </Link>
            <Link to="/terms" className="hover:text-slate-300">
              이용약관
            </Link>
            <Link to="/privacy" className="font-medium text-slate-400 hover:text-slate-200">
              개인정보 처리방침
            </Link>
          </span>
        </div>
      </footer>
    </div>
  );
}

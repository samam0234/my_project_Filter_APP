/**
 * 사용자 앱 공통 레이아웃 — 상단 내비게이션 · 서버 상태 · 푸터.
 *
 * 메뉴: 홈 / 작업실 / 작업 기록 / 프롬프트 가이드 / 배치
 * (작업 상세 /jobs/:id 는 작업 기록에서 들어가므로 메뉴에서는 "작업 기록" 을 활성으로 표시)
 */
import type { ReactNode } from "react";
import { BookOpen, History, Home, Layers, Scissors, Wand2 } from "lucide-react";
import { Link, usePathname } from "../../router";
import { useHealth } from "../../hooks/useApi";

const NAV = [
  { to: "/", label: "홈", icon: Home, match: (p: string) => p === "/" },
  { to: "/studio", label: "작업실", icon: Wand2, match: (p: string) => p.startsWith("/studio") },
  {
    to: "/history",
    label: "작업 기록",
    icon: History,
    match: (p: string) => p.startsWith("/history") || p.startsWith("/jobs"),
  },
  { to: "/guide", label: "프롬프트 가이드", icon: BookOpen, match: (p: string) => p.startsWith("/guide") },
  { to: "/batch", label: "배치", icon: Layers, match: (p: string) => p.startsWith("/batch") },
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

export function AppLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
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
            {NAV.map(({ to, label, icon: Icon, match }) => {
              const active = match(pathname);
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
                </Link>
              );
            })}
          </nav>
          <ServerStatus />
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>

      <footer className="border-t border-slate-800/80">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-slate-500">
          <span>Cut &amp; Keep · 프롬프트로 원하는 것만 남기기</span>
          <span>YOLO26s-seg · LangGraph · OpenCV · Ollama / LoRA</span>
        </div>
      </footer>
    </div>
  );
}

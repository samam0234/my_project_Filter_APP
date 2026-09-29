/**
 * 로그인 회원 전용 화면 게이트.
 *
 * - 로그인 상태 확인 중: 로딩
 * - 비로그인: 잠금 안내 + 로그인(돌아올 곳 next) · 회원가입
 * - 로그인: children
 */
import type { ReactNode } from "react";
import { Lock } from "lucide-react";
import { Link, usePathname, useSearch } from "../../router";
import { useAuthStore } from "../../store/useAuthStore";
import { LoadingBlock } from "../common/States";

interface Props {
  title: string;
  reason: string;
  children: ReactNode;
}

export function RequireLogin({ title, reason, children }: Props) {
  const status = useAuthStore((s) => s.status);
  const pathname = usePathname();
  const search = useSearch();

  if (status === "loading") return <LoadingBlock label="로그인 상태 확인 중…" />;
  if (status === "user") return <>{children}</>;

  const next = encodeURIComponent(pathname + search);
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/50 px-6 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800">
        <Lock className="h-5 w-5 text-brand-500" />
      </span>
      <div className="space-y-1">
        <h1 className="text-xl font-semibold text-white">{title}</h1>
        <p className="text-sm text-slate-400">{reason}</p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        <Link
          to={`/login?next=${next}`}
          className="rounded-xl bg-brand-600 px-5 py-2 text-sm font-medium text-white hover:bg-brand-500"
        >
          로그인
        </Link>
        <Link
          to={`/signup?next=${next}`}
          className="rounded-xl border border-slate-700 px-5 py-2 text-sm text-slate-200 hover:border-slate-500"
        >
          회원가입
        </Link>
      </div>
      <p className="text-xs text-slate-500">
        로그인하지 않아도{" "}
        <Link to="/studio" className="text-brand-500 hover:text-brand-100">
          작업실
        </Link>
        에서 배경 제거 후 바로 다운로드할 수 있어요.
      </p>
    </div>
  );
}

/**
 * 404 — 없는 경로.
 */
import { Compass } from "lucide-react";
import { Link } from "../router";
import { buttonClass } from "../components/common/Button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/70 ring-1 ring-inset ring-slate-700/60">
        <Compass className="h-7 w-7 text-slate-400" />
      </span>
      <p className="bg-gradient-to-b from-slate-300 to-slate-600 bg-clip-text text-6xl font-extrabold text-transparent">404</p>
      <p className="text-slate-300">페이지를 찾을 수 없어요.</p>
      <Link to="/" className={buttonClass("secondary", "md")}>
        홈으로
      </Link>
    </div>
  );
}

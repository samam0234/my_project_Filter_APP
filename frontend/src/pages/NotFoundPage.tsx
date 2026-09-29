/**
 * 404 — 없는 경로.
 */
import { Link } from "../router";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-3 py-24 text-center">
      <p className="text-5xl font-bold text-slate-700">404</p>
      <p className="text-slate-300">페이지를 찾을 수 없어요.</p>
      <Link to="/" className="text-sm text-brand-500 hover:text-brand-100">
        홈으로
      </Link>
    </div>
  );
}

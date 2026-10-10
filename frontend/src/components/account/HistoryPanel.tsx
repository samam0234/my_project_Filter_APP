/**
 * 작업 기록 — 내 계정(/account?tab=history) 안의 한 구역. 본인 작업만 (사진 · 영상 · GIF). 종류 · 상태 필터 · 검색.
 *
 * 필터는 URL 쿼리(?tab=history&kind=video&status=failed&q=사람)에 남겨 새로고침해도 유지한다.
 * 로그인 확인은 계정 페이지가 한다.
 */
import { useMemo } from "react";
import { RefreshCw, Search } from "lucide-react";
import { Button } from "../common/Button";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../common/States";
import { JobCard } from "../jobs/JobCard";
import { useJobs } from "../../hooks/useApi";
import { Link, navigate, usePathname, useSearch } from "../../router";
import { statusLabel } from "../../utils/formatters";

const FILTERS = ["all", "ok", "fallback", "failed"] as const;
const KINDS = [
  { id: "all", label: "전체" },
  { id: "image", label: "사진" },
  { id: "video", label: "영상" },
  { id: "gif", label: "GIF" },
] as const;

// 【수동】 한 번에 불러올 개수 (백엔드 상한 200)
const LIMIT = 120;

export function HistoryPanel() {
  const pathname = usePathname();
  const search = useSearch();
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const status = params.get("status") ?? "all";
  const kind = params.get("kind") ?? "all";
  const q = params.get("q") ?? "";
  const { data, error, loading, reload } = useJobs(LIMIT);

  const setQuery = (key: string, value: string) => {
    const next = new URLSearchParams(search);
    if (!value || value === "all") next.delete(key);
    else next.set(key, value);
    const qs = next.toString();
    navigate(`${pathname}${qs ? `?${qs}` : ""}`, { replace: true });
  };

  const counts = useMemo(() => {
    // 상태 개수는 고른 종류 안에서, 종류 개수는 전체에서 센다
    const c: Record<string, number> = { all: 0, ok: 0, fallback: 0, failed: 0 };
    const k: Record<string, number> = { all: data?.length ?? 0, image: 0, video: 0, gif: 0 };
    data?.forEach((j) => {
      const jk = j.kind ?? "image";
      k[jk] = (k[jk] ?? 0) + 1;
      if (kind !== "all" && jk !== kind) return;
      c.all += 1;
      c[j.status] = (c[j.status] ?? 0) + 1;
    });
    return { status: c, kind: k };
  }, [data, kind]);

  const jobs = useMemo(
    () =>
      (data ?? []).filter(
        (j) =>
          (kind === "all" || (j.kind ?? "image") === kind) &&
          (status === "all" || j.status === status) &&
          (!q.trim() || j.prompt.toLowerCase().includes(q.trim().toLowerCase())),
      ),
    [data, kind, status, q],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm leading-relaxed text-slate-400">
          {`내가 로그인해서 처리한 사진 · 영상 · GIF 를 최근 ${LIMIT}건까지 보여줍니다. 결과 파일은 서버 보관 시간(기본 24시간)이 지나면 지워질 수 있어요.`}
        </p>
        <Button variant="secondary" onClick={reload} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> 새로고침
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div role="tablist" aria-label="작업 종류" className="flex flex-wrap gap-1 rounded-xl border border-slate-800 bg-slate-900/50 p-1">
          {KINDS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={kind === id}
              onClick={() => setQuery("kind", id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                kind === id ? "bg-slate-800 text-white shadow-card" : "text-slate-400 hover:text-slate-100"
              }`}
            >
              {label} <span className="text-slate-500">{counts.kind[id] ?? 0}</span>
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-1 rounded-xl border border-slate-800 p-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setQuery("status", f)}
              className={`rounded-lg px-3 py-1.5 text-xs transition ${
                status === f ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-100"
              }`}
            >
              {f === "all" ? "모든 상태" : statusLabel(f)} <span className="text-slate-500">{counts.status[f] ?? 0}</span>
            </button>
          ))}
        </div>
        <label className="relative min-w-[200px] flex-1 sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQuery("q", e.target.value)}
            placeholder="프롬프트 검색"
            className="field py-2 pl-9"
          />
        </label>
      </div>

      {loading && !data ? (
        <LoadingBlock />
      ) : error ? (
        <ErrorBlock message={error} onRetry={reload} />
      ) : jobs.length === 0 ? (
        <EmptyBlock title={data?.length ? "조건에 맞는 작업이 없어요" : "아직 작업이 없어요"}>
          <Link to="/studio" className="text-brand-400 hover:text-brand-200">
            작업실로 가기
          </Link>
        </EmptyBlock>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {jobs.map((job) => (
            <JobCard key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}

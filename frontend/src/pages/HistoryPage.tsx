/**
 * 작업 기록 (/history) — 최근 작업 그리드 · 상태 필터 · 검색.
 *
 * 필터는 URL 쿼리(?status=failed&q=사람)에 남겨 새로고침·공유해도 유지한다.
 */
import { useMemo } from "react";
import { RefreshCw, Search } from "lucide-react";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../components/common/States";
import { JobCard } from "../components/jobs/JobCard";
import { useJobs } from "../hooks/useApi";
import { Link, navigate, useSearch } from "../router";
import { statusLabel } from "../utils/formatters";

const FILTERS = ["all", "ok", "fallback", "failed"] as const;

// 【수동】 한 번에 불러올 개수 (백엔드 상한 200)
const LIMIT = 120;

export function HistoryPage() {
  const search = useSearch();
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const status = params.get("status") ?? "all";
  const q = params.get("q") ?? "";
  const { data, error, loading, reload } = useJobs(LIMIT);

  const setQuery = (key: string, value: string) => {
    const next = new URLSearchParams(search);
    if (!value || value === "all") next.delete(key);
    else next.set(key, value);
    const qs = next.toString();
    navigate(`/history${qs ? `?${qs}` : ""}`, { replace: true });
  };

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: data?.length ?? 0, ok: 0, fallback: 0, failed: 0 };
    data?.forEach((j) => {
      c[j.status] = (c[j.status] ?? 0) + 1;
    });
    return c;
  }, [data]);

  const jobs = useMemo(
    () =>
      (data ?? []).filter(
        (j) =>
          (status === "all" || j.status === status) &&
          (!q.trim() || j.prompt.toLowerCase().includes(q.trim().toLowerCase())),
      ),
    [data, status, q],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="작업 기록"
        title="지금까지의 작업"
        description={`최근 ${LIMIT}건까지 보여줍니다. 결과 파일은 서버 보관 시간(기본 24시간)이 지나면 지워질 수 있어요.`}
        actions={
          <Button variant="secondary" onClick={reload} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> 새로고침
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
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
              {f === "all" ? "전체" : statusLabel(f)} <span className="text-slate-500">{counts[f] ?? 0}</span>
            </button>
          ))}
        </div>
        <label className="relative min-w-[200px] flex-1 sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQuery("q", e.target.value)}
            placeholder="프롬프트 검색"
            className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2 pl-9 pr-3 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-brand-500"
          />
        </label>
      </div>

      {loading && !data ? (
        <LoadingBlock />
      ) : error ? (
        <ErrorBlock message={error} onRetry={reload} />
      ) : jobs.length === 0 ? (
        <EmptyBlock title={data?.length ? "조건에 맞는 작업이 없어요" : "아직 작업이 없어요"}>
          <Link to="/studio" className="text-brand-500 hover:text-brand-100">
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

import { StatCard } from "../components/StatCard";
import { useConsoleStore } from "../store/useConsoleStore";

export function DashboardPage() {
  const health = useConsoleStore((s) => s.health);
  const jobs = useConsoleStore((s) => s.jobs);
  const lastRefreshed = useConsoleStore((s) => s.lastRefreshed);

  const ok = jobs.filter((j) => j.status === "ok").length;
  const failed = jobs.filter((j) => j.status === "failed").length;
  const fallback = jobs.filter((j) => j.status === "fallback").length;
  const withFeedback = jobs.filter((j) => j.feedback_saved).length;
  const avgQuality =
    jobs.length > 0
      ? jobs.reduce((s, j) => s + (j.quality_score || 0), 0) / jobs.length
      : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white">운영 대시보드</h2>
        <p className="mt-1 text-sm text-console-muted">
          처리 Job·헬스·피드백 요약. 마지막 갱신:{" "}
          {lastRefreshed
            ? new Date(lastRefreshed).toLocaleString("ko-KR")
            : "아직 없음"}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="API 상태"
          value={health?.status || "unknown"}
          hint={`v${health?.version || "-"} · phase ${health?.phase ?? "-"}`}
          tone={health?.status === "ok" ? "ok" : "bad"}
        />
        <StatCard
          label="DB dialect"
          value={health?.db_dialect || "-"}
          hint="sqlite(local) / mysql(MariaDB)"
        />
        <StatCard label="총 Job" value={jobs.length} hint="최근 조회 목록 기준" />
        <StatCard
          label="평균 quality"
          value={`${Math.round(avgQuality * 100)}%`}
          tone={avgQuality >= 0.5 ? "ok" : "warn"}
        />
        <StatCard label="ok" value={ok} tone="ok" />
        <StatCard label="fallback" value={fallback} tone="warn" />
        <StatCard label="failed" value={failed} tone={failed ? "bad" : "default"} />
        <StatCard label="feedback 저장" value={withFeedback} />
      </div>

      <section className="rounded-xl border border-console-border bg-console-panel p-4">
        <h3 className="text-sm font-semibold text-white">최근 Job (5)</h3>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs text-console-muted">
              <tr>
                <th className="px-2 py-2">job_id</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">prompt</th>
                <th className="px-2 py-2">quality</th>
              </tr>
            </thead>
            <tbody>
              {jobs.slice(0, 5).map((j) => (
                <tr key={j.job_id} className="border-t border-console-border">
                  <td className="px-2 py-2 font-mono text-xs text-console-accent">
                    {j.job_id.slice(0, 10)}…
                  </td>
                  <td className="px-2 py-2">{j.status}</td>
                  <td className="max-w-xs truncate px-2 py-2 text-slate-300">
                    {j.prompt}
                  </td>
                  <td className="px-2 py-2">
                    {Math.round((j.quality_score || 0) * 100)}%
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-2 py-6 text-center text-console-muted"
                  >
                    아직 Job이 없습니다. 사용자 앱에서 업로드 후 새로고침하세요.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

import { resolveAssetUrl } from "../api/client";
import { useConsoleStore } from "../store/useConsoleStore";

export function JobsPage() {
  const jobs = useConsoleStore((s) => s.jobs);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">Job 관리</h2>
        <p className="mt-1 text-sm text-console-muted">
          `GET /api/v1/jobs` — DB에 저장된 처리 이력
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-console-border bg-console-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-xs uppercase text-console-muted">
              <tr>
                <th className="px-3 py-3">Job ID</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Prompt</th>
                <th className="px-3 py-3">Backend</th>
                <th className="px-3 py-3">Quality</th>
                <th className="px-3 py-3">Feedback</th>
                <th className="px-3 py-3">Created</th>
                <th className="px-3 py-3">Preview</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr
                  key={j.job_id}
                  className="border-t border-console-border align-top"
                >
                  <td className="px-3 py-3 font-mono text-xs text-console-accent">
                    {j.job_id}
                  </td>
                  <td className="px-3 py-3">
                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs">
                      {j.status}
                    </span>
                  </td>
                  <td className="max-w-xs px-3 py-3 text-slate-300">{j.prompt}</td>
                  <td className="px-3 py-3 text-xs">{j.backend || "-"}</td>
                  <td className="px-3 py-3">
                    {Math.round((j.quality_score || 0) * 100)}%
                  </td>
                  <td className="px-3 py-3">
                    {j.feedback_saved ? "yes" : "no"}
                  </td>
                  <td className="px-3 py-3 text-xs text-console-muted">
                    {j.created_at
                      ? new Date(j.created_at).toLocaleString("ko-KR")
                      : "-"}
                  </td>
                  <td className="px-3 py-3">
                    {j.after_url ? (
                      <a
                        href={resolveAssetUrl(j.after_url)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-console-accent underline"
                      >
                        after
                      </a>
                    ) : (
                      <span className="text-xs text-console-muted">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-3 py-10 text-center text-console-muted"
                  >
                    Job 데이터가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

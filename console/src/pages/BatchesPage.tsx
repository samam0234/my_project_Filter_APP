/**
 * 배치 현황 (전체 회원) — `GET /api/v1/console/batches`.
 *
 * 처리 상태·진행·실패 수를 한눈에. 이미지는 보여 주지 않는다 (회원의 사진이라 운영 화면에 노출하지 않음).
 * 진행 중인 배치가 있으면 5초마다 자동 갱신한다.
 */
import { useCallback, useEffect, useState } from "react";
import { fetchBatches } from "../api/client";
import { StatCard } from "../components/StatCard";
import type { BatchSummary } from "../types";

const STATUS_STYLE: Record<string, string> = {
  queued: "bg-slate-800 text-slate-200",
  running: "bg-sky-900/50 text-sky-300",
  done: "bg-emerald-900/50 text-emerald-300",
  failed: "bg-rose-900/40 text-rose-300",
};

export function BatchesPage() {
  const [rows, setRows] = useState<BatchSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await fetchBatches(100));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const active = rows.some((r) => r.status === "queued" || r.status === "running");
  useEffect(() => {
    if (!active) return;
    const t = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(t);
  }, [active, load]);

  const count = (s: string) => rows.filter((r) => r.status === s).length;
  const failedItems = rows.reduce((n, r) => n + (r.failed ?? 0), 0);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">배치 현황</h2>
        <p className="mt-1 text-sm text-console-muted">
          `GET /api/v1/console/batches` — 전체 회원의 최근 배치 (이미지는 표시하지 않음 · 관리자 로그인 또는 서버 PC 에서만 조회 가능)
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="진행 중" value={count("queued") + count("running")} tone={active ? "warn" : "default"} />
        <StatCard label="완료" value={count("done")} tone="ok" />
        <StatCard label="전체 실패" value={count("failed")} tone={count("failed") ? "bad" : "default"} />
        <StatCard label="실패한 장" value={failedItems} hint="완료된 배치 안에서 처리하지 못한 사진" />
      </div>

      {error && (
        <div className="rounded-xl border border-amber-800/40 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">{error}</div>
      )}

      <div className="overflow-hidden rounded-xl border border-console-border bg-console-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-xs uppercase text-console-muted">
              <tr>
                <th className="px-3 py-3">Batch ID</th>
                <th className="px-3 py-3">상태</th>
                <th className="px-3 py-3">문장</th>
                <th className="px-3 py-3">진행</th>
                <th className="px-3 py-3">실패</th>
                <th className="px-3 py-3">회원</th>
                <th className="px-3 py-3">등록</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.job_id} className="border-t border-console-border align-top">
                  <td className="px-3 py-3 font-mono text-xs text-console-accent">{r.job_id.slice(0, 12)}…</td>
                  <td className="px-3 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[r.status] ?? "bg-slate-800"}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="max-w-xs px-3 py-3 text-slate-300">{r.prompt || "-"}</td>
                  <td className="px-3 py-3 text-xs">
                    {r.completed ?? 0}/{r.total ?? "-"} · {Math.round((r.progress ?? 0) * 100)}%
                  </td>
                  <td className="px-3 py-3 text-xs">{r.failed ? <span className="text-rose-300">{r.failed}</span> : "0"}</td>
                  <td className="px-3 py-3 font-mono text-xs text-console-muted">{r.user_id?.slice(0, 8) ?? "-"}</td>
                  <td className="px-3 py-3 text-xs text-console-muted">
                    {r.created_at ? new Date(r.created_at).toLocaleString("ko-KR") : "-"}
                  </td>
                </tr>
              ))}
              {loaded && rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-10 text-center text-console-muted">
                    아직 등록된 배치가 없습니다.
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

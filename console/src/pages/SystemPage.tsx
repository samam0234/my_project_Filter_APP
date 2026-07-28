/**
 * 시스템 정보: /health 필드 + 포트·프록시 메모.
 * 연결 실패 시 store.error 를 이 페이지에서 강조 표시.
 */
import { useConsoleStore } from "../store/useConsoleStore";

export function SystemPage() {
  const health = useConsoleStore((s) => s.health);
  const error = useConsoleStore((s) => s.error);

  // 키-값 목록 (테이블 대신 dl)
  const rows = [
    { k: "status", v: health?.status ?? "-" },
    { k: "version", v: health?.version ?? "-" },
    { k: "phase", v: String(health?.phase ?? "-") },
    { k: "db_dialect", v: health?.db_dialect ?? "-" },
    {
      k: "API base",
      v: import.meta.env.VITE_API_BASE_URL || "(proxy / same origin)",
    },
    { k: "console port", v: "5174 (dev)" },
    { k: "user app port", v: "5173 (frontend)" },
    { k: "backend port", v: "8000" },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">시스템 정보</h2>
        <p className="mt-1 text-sm text-console-muted">
          헬스체크 · 런타임 연결 정보
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-console-border bg-console-panel">
        <dl className="divide-y divide-console-border">
          {rows.map((r) => (
            <div
              key={r.k}
              className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <dt className="text-xs uppercase tracking-wide text-console-muted">
                {r.k}
              </dt>
              <dd className="font-mono text-sm text-slate-200">{r.v}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="rounded-xl border border-console-border bg-console-panel p-4 text-sm text-console-muted">
        <p className="font-medium text-slate-200">운영 메모</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Docker 스택 프로젝트명: <code>cut_and_keep</code></li>
          <li>MariaDB 호스트 포트: 3306 / Redis 호스트 포트: 6380</li>
          <li>상세 트러블슈팅: <code>docs/repeater/</code></li>
        </ul>
      </div>
    </div>
  );
}

import { useAppStore } from "../../store/useAppStore";
import { formatScore } from "../../utils/formatters";

export function BeforeAfterViewer() {
  const result = useAppStore((s) => s.result);
  if (!result) return null;

  return (
    <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-100">결과</h3>
        <div className="flex gap-2 text-xs">
          <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-300">
            status: {result.status}
          </span>
          <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-300">
            quality: {formatScore(result.qualityScore)}
          </span>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <figure className="space-y-2">
          <figcaption className="text-xs text-slate-400">Before</figcaption>
          {result.beforeUrl ? (
            <img
              src={result.beforeUrl}
              alt="before"
              className="w-full rounded-xl border border-slate-800 object-contain"
            />
          ) : (
            <div className="flex h-40 items-center justify-center rounded-xl bg-slate-800 text-xs text-slate-500">
              no before
            </div>
          )}
        </figure>
        <figure className="space-y-2">
          <figcaption className="text-xs text-slate-400">After</figcaption>
          {result.afterUrl ? (
            <img
              src={result.afterUrl}
              alt="after"
              className="w-full rounded-xl border border-slate-800 object-contain bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2216%22 height=%2216%22><rect width=%228%22 height=%228%22 fill=%22%23334155%22/><rect x=%228%22 y=%228%22 width=%228%22 height=%228%22 fill=%22%23334155%22/></svg>')] bg-[length:16px_16px]"
            />
          ) : (
            <div className="flex h-40 items-center justify-center rounded-xl bg-slate-800 text-xs text-slate-500">
              no after
            </div>
          )}
        </figure>
      </div>
      {result.parsedPrompt && (
        <pre className="overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-400">
          {JSON.stringify(result.parsedPrompt, null, 2)}
        </pre>
      )}
      {result.message && (
        <p className="text-xs text-amber-400/90">{result.message}</p>
      )}
    </div>
  );
}

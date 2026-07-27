/**
 * Phase 2 — multi-image batch upload UI scaffold.
 * Max 500 images via Celery + Redis when backend is ready.
 */
export function BatchUploader() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-4 text-sm text-slate-400">
      <p className="font-medium text-slate-300">배치 업로드 (Phase 2)</p>
      <p className="mt-1 text-xs">
        최대 500장 · Celery + Redis · 진행률 UI는 Phase 2에서 활성화됩니다.
      </p>
    </div>
  );
}

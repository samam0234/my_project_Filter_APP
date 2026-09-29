/**
 * 배치 (/batch) — 여러 장을 한 문장으로 등록 · 상태 조회.
 *
 * 백엔드 배치 워커는 Phase 2 (backend/app/tasks/batch_tasks.py 하드코딩 구간).
 * 지금은 등록(batch_jobs 기록)과 상태 조회만 동작하며, 화면에 그 사실을 분명히 표시한다.
 */
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Info, Layers, Search, X } from "lucide-react";
import { createBatch, errorMessage, getBatch } from "../api/client";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import type { BatchStatus } from "../types";
import { formatFileSize } from "../utils/formatters";

// 【수동】 백엔드 MAX_BATCH_SIZE(500) · MAX_UPLOAD_SIZE_MB(20) 와 맞춤
const MAX_FILES = 500;
const MAX_SIZE = 20 * 1024 * 1024;

function StatusCard({ status }: { status: BatchStatus }) {
  const progress = Math.round((status.progress ?? 0) * 100);
  return (
    <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <code className="break-all text-xs text-slate-300">{status.job_id}</code>
        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">{status.status}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <p className="text-xs text-slate-400">
        {status.completed ?? 0} / {status.total ?? "-"} 장 · {progress}%
      </p>
      {status.message && <p className="text-xs text-amber-200/90">{status.message}</p>}
    </div>
  );
}

export function BatchPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [prompt, setPrompt] = useState("사람만 남기고 배경 제거");
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState<BatchStatus | null>(null);
  const [lookupId, setLookupId] = useState("");
  const [lookup, setLookup] = useState<BatchStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted].slice(0, MAX_FILES));
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "image/webp": [".webp"] },
    maxSize: MAX_SIZE,
    multiple: true,
  });
  const totalSize = files.reduce((n, f) => n + f.size, 0);

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await createBatch(files, prompt.trim());
      setCreated(res);
      setLookupId(res.job_id);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const find = async () => {
    if (!lookupId.trim()) return;
    setError(null);
    try {
      setLookup(await getBatch(lookupId.trim()));
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="배치"
        title="여러 장을 한 번에"
        description={`같은 문장으로 최대 ${MAX_FILES}장을 등록합니다.`}
      />

      <div className="flex gap-3 rounded-2xl border border-amber-800/40 bg-amber-950/20 p-4 text-sm text-amber-100/90">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          준비 중인 기능입니다 (Phase 2). 지금은 <b>등록과 상태 조회만</b> 되고 실제 처리는 아직 실행되지 않아요.
          한 장씩 처리는 작업실을 이용해 주세요.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="space-y-4">
          <div
            {...getRootProps()}
            className={`cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition ${
              isDragActive ? "border-brand-500 bg-brand-500/10" : "border-slate-700 bg-slate-900/60 hover:border-slate-500"
            }`}
          >
            <input {...getInputProps()} />
            <Layers className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm text-slate-100">이미지 여러 장을 드래그하거나 클릭</p>
            <p className="text-xs text-slate-500">JPEG / PNG / WebP · 장당 20MB · 최대 {MAX_FILES}장</p>
          </div>

          {files.length > 0 && (
            <div className="space-y-2 rounded-2xl border border-slate-800 p-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>
                  {files.length}장 · {formatFileSize(totalSize)}
                </span>
                <button type="button" onClick={() => setFiles([])} className="hover:text-white">
                  모두 비우기
                </button>
              </div>
              <ul className="max-h-48 space-y-1 overflow-auto text-xs">
                {files.map((f, i) => (
                  <li key={`${f.name}-${i}`} className="flex items-center gap-2 text-slate-300">
                    <span className="min-w-0 flex-1 truncate">{f.name}</span>
                    <span className="text-slate-500">{formatFileSize(f.size)}</span>
                    <button
                      type="button"
                      aria-label={`${f.name} 빼기`}
                      onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                      className="text-slate-500 hover:text-white"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <label className="block space-y-2">
            <span className="text-sm text-slate-200">모든 사진에 적용할 문장</span>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-brand-500"
            />
          </label>
          <Button onClick={() => void submit()} disabled={submitting || !files.length || !prompt.trim()}>
            {submitting ? "등록 중…" : `${files.length}장 등록`}
          </Button>
          {created && <StatusCard status={created} />}
        </section>

        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-200">배치 상태 조회</h2>
          <div className="flex gap-2">
            <input
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void find()}
              placeholder="배치 ID"
              className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-brand-500"
            />
            <Button variant="secondary" onClick={() => void find()} disabled={!lookupId.trim()}>
              <Search className="h-4 w-4" /> 조회
            </Button>
          </div>
          {lookup && <StatusCard status={lookup} />}
          {error && (
            <p className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
              {error}
            </p>
          )}
        </section>
      </div>
    </div>
  );
}

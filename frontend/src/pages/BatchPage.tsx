/**
 * 배치 (/batch) — 여러 장을 한 문장으로 등록 · 진행률 · 항목별 결과 · zip 다운로드.
 *
 * 로그인 회원 전용 (백엔드도 로그인 필수 · 본인 배치만).
 * 등록하면 서버가 한 장씩 단일 업로드와 같은 파이프라인으로 처리하고, 화면은 2초마다 상태를 갱신한다.
 * 결과·원본은 서버에 24시간만 보관된다 (FILE_RETENTION_HOURS) — 만료되면 이미지가 사라지고 기록만 남는다.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Clock, Download, Layers, Loader2, RefreshCw, X } from "lucide-react";
import { createBatch, downloadFile, errorMessage, getBatch, listBatches, resolveAssetUrl } from "../api/client";
import { RequireLogin } from "../components/auth/RequireLogin";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { ResultImage } from "../components/image/ResultImage";
import type { BatchItem, BatchStatus, BatchSummary } from "../types";
import { formatFileSize, formatRelative } from "../utils/formatters";

// 【수동】 백엔드 MAX_BATCH_SIZE(500) · MAX_UPLOAD_SIZE_MB(20) 와 맞춤
const MAX_FILES = 500;
const MAX_SIZE = 20 * 1024 * 1024;
const POLL_MS = 2000;
const FINISHED = new Set(["done", "failed", "not_found"]);

const STATUS_LABEL: Record<string, string> = {
  queued: "대기 중",
  running: "처리 중",
  done: "완료",
  failed: "실패",
  not_found: "없음",
};
const ITEM_LABEL: Record<string, string> = { ok: "완료", fallback: "부분 성공", failed: "실패" };

/** 상태를 처리가 끝날 때까지 주기적으로 가져온다. id 가 바뀌거나 사라지면 멈춘다. */
export function useBatchPolling(jobId: string | null, intervalMs = POLL_MS) {
  const [status, setStatus] = useState<BatchStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setStatus(null);
    setError(null);
    if (!jobId) return;
    let stopped = false;
    let timer: number | undefined;
    const tick = async () => {
      try {
        const next = await getBatch(jobId);
        if (stopped) return;
        setStatus(next);
        setError(null);
        if (!FINISHED.has(next.status)) timer = window.setTimeout(tick, intervalMs);
      } catch (err) {
        if (stopped) return;
        setError(errorMessage(err));
        timer = window.setTimeout(tick, intervalMs * 2); // 일시적인 오류면 느리게 다시
      }
    };
    void tick();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [jobId, intervalMs]);

  return { status, error };
}

function ProgressCard({ status }: { status: BatchStatus }) {
  const progress = Math.round((status.progress ?? 0) * 100);
  const running = !FINISHED.has(status.status);
  return (
    <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <code className="break-all text-xs text-slate-400">{status.job_id}</code>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-200">
          {running && <Loader2 className="h-3 w-3 animate-spin" />}
          {STATUS_LABEL[status.status] ?? status.status}
        </span>
      </div>
      {status.prompt && <p className="text-slate-200">“{status.prompt}”</p>}
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full bg-brand-500 transition-all" style={{ width: `${progress}%` }} />
      </div>
      <p className="text-xs text-slate-400">
        {status.completed ?? 0} / {status.total ?? "-"} 장 · {progress}%
        {status.message ? ` · ${status.message}` : ""}
      </p>
    </div>
  );
}

function ItemCard({ item }: { item: BatchItem }) {
  const failed = !item.after_url;
  return (
    <li className="space-y-2 rounded-xl border border-slate-800 bg-slate-900/40 p-2">
      <div className="grid grid-cols-2 gap-2">
        <ResultImage src={resolveAssetUrl(item.before_url) ?? ""} alt={`${item.filename} 원본`} />
        {failed ? (
          <div className="flex items-center justify-center rounded-lg bg-rose-950/30 p-2 text-center text-xs text-rose-200">
            처리하지 못했어요
          </div>
        ) : (
          <ResultImage src={resolveAssetUrl(item.after_url) ?? ""} alt={`${item.filename} 결과`} checker />
        )}
      </div>
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="min-w-0 flex-1 truncate text-slate-300" title={item.filename}>
          {item.filename}
        </span>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 ${
            item.status === "ok" ? "bg-emerald-900/50 text-emerald-300" : "bg-rose-900/40 text-rose-300"
          }`}
        >
          {ITEM_LABEL[item.status] ?? item.status}
        </span>
      </div>
      {item.message && item.status !== "ok" && <p className="text-xs text-amber-200/90">{item.message}</p>}
    </li>
  );
}

export function BatchPage() {
  return (
    <RequireLogin title="배치는 로그인 회원 전용이에요" reason="여러 장을 한 번에 처리하고 결과를 받으려면 로그인해 주세요.">
      <Batch />
    </RequireLogin>
  );
}

function Batch() {
  const [files, setFiles] = useState<File[]>([]);
  const [prompt, setPrompt] = useState("사람만 남기고 배경 제거");
  const [submitting, setSubmitting] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mine, setMine] = useState<BatchSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const { status, error: pollError } = useBatchPolling(activeId);

  const loadMine = useCallback(async () => {
    try {
      setMine(await listBatches());
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    void loadMine();
  }, [loadMine]);

  // 처리가 끝나면 목록의 진행 상태도 갱신
  const lastStatus = useRef<string | null>(null);
  useEffect(() => {
    if (status && status.status !== lastStatus.current && FINISHED.has(status.status)) void loadMine();
    lastStatus.current = status?.status ?? null;
  }, [status, loadMine]);

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
      setFiles([]);
      setActiveId(res.job_id);
      void loadMine();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const downloadZip = async () => {
    if (!status?.download_url) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadFile(status.download_url, `cutnkeep_batch_${status.job_id.slice(0, 8)}.zip`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  const items = status?.item_results ?? [];
  const finished = status ? FINISHED.has(status.status) : false;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="배치"
        title="여러 장을 한 번에"
        description={`같은 문장으로 최대 ${MAX_FILES}장을 처리해요. 한 장씩 작업실과 같은 방식으로 처리되고, 진행 상황이 자동으로 갱신됩니다.`}
      />

      <p className="flex items-center gap-2 text-xs text-slate-500">
        <Clock className="h-3.5 w-3.5 shrink-0" />
        원본과 결과는 서버에 <b className="text-slate-400">24시간</b>만 보관돼요. 필요한 결과는 그 안에 내려받아 주세요.
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <section className="space-y-4 lg:col-span-2">
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
            {submitting ? "올리는 중…" : files.length ? `${files.length}장 처리 시작` : "처리 시작"}
          </Button>

          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-200">내 배치</h2>
              <button
                type="button"
                aria-label="목록 새로고침"
                onClick={() => void loadMine()}
                className="text-slate-500 hover:text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
            {mine.length === 0 ? (
              <p className="text-xs text-slate-500">아직 처리한 배치가 없어요.</p>
            ) : (
              <ul className="space-y-1">
                {mine.map((b) => (
                  <li key={b.job_id}>
                    <button
                      type="button"
                      onClick={() => setActiveId(b.job_id)}
                      className={`w-full rounded-xl border px-3 py-2 text-left text-xs transition ${
                        activeId === b.job_id
                          ? "border-brand-500 bg-brand-500/10"
                          : "border-slate-800 bg-slate-900/40 hover:border-slate-600"
                      }`}
                    >
                      <span className="block truncate text-slate-200">{b.prompt || b.job_id}</span>
                      <span className="text-slate-500">
                        {STATUS_LABEL[b.status] ?? b.status} · {b.completed ?? 0}/{b.total ?? "-"}장 ·{" "}
                        {formatRelative(b.created_at)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="space-y-4 lg:col-span-3">
          {!status && !activeId && (
            <p className="rounded-2xl border border-dashed border-slate-800 py-16 text-center text-sm text-slate-500">
              사진을 올려 처리하거나, 왼쪽 “내 배치”에서 고르면 결과가 여기에 보여요.
            </p>
          )}
          {status && (
            <>
              <ProgressCard status={status} />
              {finished && status.status !== "not_found" && (
                <div className="flex flex-wrap items-center gap-3">
                  <Button onClick={() => void downloadZip()} disabled={!status.download_url || downloading}>
                    <Download className="h-4 w-4" /> {downloading ? "받는 중…" : "결과 모두 받기 (zip)"}
                  </Button>
                  {!status.download_url && <span className="text-xs text-slate-500">받을 결과가 없어요.</span>}
                </div>
              )}
              {items.length > 0 && (
                <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {items.map((item) => (
                    <ItemCard key={item.index} item={item} />
                  ))}
                </ul>
              )}
            </>
          )}
          {(error || pollError) && (
            <p className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
              {error ?? pollError}
            </p>
          )}
        </section>
      </div>
    </div>
  );
}

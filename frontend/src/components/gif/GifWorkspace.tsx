/**
 * 작업실 GIF 탭 — 움직이는 GIF 한 개를 프레임마다 처리해 다시 GIF 로.
 *
 * - 문장은 사진 탭과 같은 useAppStore.prompt 를 쓴다 (탭을 바꿔도 유지)
 * - 회원: 서버에 보관되고 작업 기록에 GIF 로 남는다 · 비로그인: 결과는 data URL 로 와서 내려받기만
 * - 배경 제거는 투명 GIF(1비트 투명) — 부드러운 경계가 필요하면 사진(PNG)으로 처리
 */
import { useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ExternalLink, Film, Loader2, RefreshCw, RotateCcw, Wand2 } from "lucide-react";
import { errorMessage, processGif, resolveAssetUrl } from "../../api/client";
import type { GifResponse } from "../../types";
import { Link } from "../../router";
import { useAppStore } from "../../store/useAppStore";
import { useAuthStore } from "../../store/useAuthStore";
import { formatFileSize } from "../../utils/formatters";
import { Button } from "../common/Button";
import { Step } from "../common/Step";
import { FeedbackPanel } from "../feedback/FeedbackPanel";
import { BeforeAfterViewer } from "../image/BeforeAfterViewer";
import { PromptInput } from "../prompt/PromptInput";

// 【수동】 백엔드 MAX_UPLOAD_SIZE_MB · GIF_MAX_FRAMES 와 맞춘다
const MAX_MB = 20;
const MAX_FRAMES = 120;

export function GifWorkspace() {
  const prompt = useAppStore((s) => s.prompt);
  const guest = useAuthStore((s) => s.status === "guest");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<GifResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const preview = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => void (preview && URL.revokeObjectURL(preview)), [preview]);

  useEffect(() => {
    if (!busy) return;
    setElapsed(0);
    const started = Date.now();
    const t = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 500);
    return () => window.clearInterval(t);
  }, [busy]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop: (accepted) => {
      if (accepted[0]) {
        setFile(accepted[0]);
        setResult(null);
        setError(null);
      }
    },
    accept: { "image/gif": [".gif"] },
    maxFiles: 1,
    maxSize: MAX_MB * 1024 * 1024,
    disabled: busy,
  });
  const rejected = fileRejections[0]?.errors[0]?.code;

  const canRun = Boolean(file && prompt.trim()) && !busy;
  const run = async () => {
    if (!file || !prompt.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await processGif(file, prompt.trim()));
    } catch (err) {
      setError(errorMessage(err, "GIF 를 처리하지 못했어요."));
    } finally {
      setBusy(false);
    }
  };
  const reset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  const before = result?.saved ? resolveAssetUrl(result.before_url) : preview;
  const after = resolveAssetUrl(result?.after_url);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div className="card space-y-7 p-5 sm:p-6">
        <Step n={1} title="GIF 올리기" done={Boolean(file)}>
          <div
            {...getRootProps()}
            className={`group relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed transition ${
              isDragActive
                ? "border-brand-400 bg-brand-500/10"
                : preview
                  ? "border-slate-700 bg-slate-950/60 hover:border-slate-500"
                  : "border-slate-700 bg-slate-900/40 hover:border-brand-500/60 hover:bg-slate-900/70"
            }`}
          >
            <input {...getInputProps()} aria-label="GIF 파일 선택" />
            {preview ? (
              <div className="relative">
                <img src={preview} alt="올린 GIF" className="mx-auto max-h-72 w-full object-contain" />
                <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 opacity-0 transition group-hover:opacity-100">
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-xs text-slate-100 ring-1 ring-slate-700">
                    <RefreshCw className="h-3.5 w-3.5" /> 다른 GIF 로 바꾸기
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 px-6 py-10 text-center">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 ring-1 ring-inset ring-brand-500/25 transition group-hover:scale-105">
                  <Film className="h-6 w-6 text-brand-400" />
                </span>
                <div>
                  <p className="font-medium text-slate-100">{isDragActive ? "여기에 놓으세요" : "GIF 드래그 또는 클릭"}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    움직이는 GIF · 최대 {MAX_MB}MB · 앞 {MAX_FRAMES}프레임까지
                  </p>
                </div>
              </div>
            )}
          </div>
          {file && (
            <p className="truncate text-xs text-slate-400">
              <span className="text-brand-300">{file.name}</span> · {formatFileSize(file.size)}
            </p>
          )}
          {rejected && (
            <p className="text-xs text-rose-300" role="alert">
              {rejected === "file-too-large" ? `${MAX_MB}MB 보다 큰 GIF 는 올릴 수 없어요.` : "GIF 파일(.gif)만 올릴 수 있어요."}
            </p>
          )}
        </Step>

        <Step n={2} title="무엇을 남기거나 지울까요?" done={Boolean(prompt.trim())}>
          <PromptInput onSubmit={() => canRun && void run()} />
        </Step>

        <Step n={3} title="처리하기">
          <div className="flex flex-wrap gap-2">
            <Button size="lg" onClick={() => void run()} disabled={!canRun} className="flex-1 sm:flex-none">
              <Wand2 className="h-4 w-4" /> GIF 처리 시작
            </Button>
            <Button variant="ghost" size="lg" onClick={reset} disabled={busy}>
              <RotateCcw className="h-4 w-4" /> 초기화
            </Button>
          </div>
          {!canRun && !busy && (
            <p className="text-xs text-slate-500">{!file ? "먼저 GIF 를 올려 주세요." : "문장을 적으면 시작할 수 있어요."}</p>
          )}
          {busy && (
            <div className="flex items-center gap-3 rounded-xl border border-brand-700/40 bg-brand-950/40 p-3.5 text-sm text-brand-100" aria-live="polite">
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-brand-300" />
              <span className="flex-1">프레임마다 대상을 찾고 있어요 — 프레임이 많을수록 오래 걸려요</span>
              <span className="tabular-nums text-xs text-brand-200/70">{elapsed}s</span>
            </div>
          )}
          {error && (
            <p className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2.5 text-sm text-rose-200" role="alert">
              {error}
            </p>
          )}
        </Step>

        <p className="border-t border-slate-800 pt-4 text-xs leading-relaxed text-slate-500">
          배경 제거는 <b className="text-slate-300">투명 GIF</b> 로 만들어요. GIF 는 반투명을 표현하지 못해 경계가 사진(PNG)보다 거칠 수 있어요.
          {guest && (
            <>
              {" "}
              <Link to="/login?next=%2Fstudio%3Ftype%3Dgif" className="text-brand-400 hover:text-brand-200">
                로그인
              </Link>
              하면 작업 기록에 GIF 로 남아요.
            </>
          )}
        </p>
      </div>

      <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
        {result ? (
          <>
            <BeforeAfterViewer
              jobId={result.job_id}
              status={result.status}
              qualityScore={null}
              beforeUrl={before}
              afterUrl={after}
              parsedPrompt={result.parsed_prompt}
              message={result.message}
              note={result.message}
              fileExt=".gif"
              extraDownload={result.webp_url ? { label: "WebP 저장 (부드러운 경계)", href: resolveAssetUrl(result.webp_url) ?? "", ext: ".webp", title: "GIF 는 반투명을 못 담아 경계가 거칠어요. WebP 는 경계를 부드럽게 유지해요 (대부분의 브라우저·메신저에서 재생)" } : null}
            />
            <p className="text-xs text-slate-500">
              {result.frames}프레임 처리{result.transparent ? " · 투명 배경" : ""}
            </p>
            {result.saved ? (
              <>
                <FeedbackPanel key={result.job_id} jobId={result.job_id} parsed={result.parsed_prompt} />
                <Link
                  to={`/jobs/${result.job_id}`}
                  className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-200"
                >
                  작업 상세 보기 <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              </>
            ) : (
              <div className="space-y-1 rounded-2xl border border-amber-800/40 bg-amber-950/20 p-4 text-sm text-amber-100/90">
                <p className="font-medium">이 결과는 저장되지 않아요</p>
                <p className="text-xs text-amber-100/70">
                  로그인하지 않은 작업은 서버에 남기지 않습니다. 필요하면 지금 <b>결과 저장</b>으로 내려받으세요.
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center text-sm text-slate-500 lg:min-h-[420px]">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/70 ring-1 ring-inset ring-slate-700/60">
              {busy ? <Loader2 className="h-6 w-6 animate-spin text-brand-300" /> : <Film className="h-6 w-6 text-slate-400" />}
            </span>
            <p className="text-slate-300">{busy ? "GIF 를 만드는 중이에요" : "처리한 GIF 가 여기에 표시됩니다."}</p>
            <p className="max-w-xs text-xs leading-relaxed">프레임마다 사진과 같은 방식으로 처리해요. 프레임이 많을수록 오래 걸려요.</p>
          </div>
        )}
      </div>
    </div>
  );
}

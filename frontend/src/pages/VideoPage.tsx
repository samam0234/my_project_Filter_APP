/**
 * 영상 (/video) — 짧은 영상 한 개에 같은 문장을 프레임마다 적용.
 *
 * 결과는 H.264 mp4(서버에 ffmpeg 가 없으면 webm → avi)라 페이지에서 바로 재생하고 저장한다.
 * 마지막 결과 1건은 이 브라우저(IndexedDB)에도 보관해 새로고침·재방문해도 다시 보고 저장할 수 있다 —
 * 비로그인은 서버에 아무것도 남지 않으므로 이 보관이 유일한 "다시 보기"다. 회원은 서버에도 24시간 보관된다.
 * 서버가 해석한 효과·강도를 보여 줘 기대와 다르면 문장을 고쳐 바로 "다시 처리"할 수 있다.
 * 처리는 동기라 길게 기다린다 (프레임마다 세그).
 */
import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Clapperboard, Download, HardDrive, Info, Loader2, RotateCcw, Trash2, X } from "lucide-react";
import { errorMessage, fetchBlob, processVideo, saveBlob } from "../api/client";
import { ModelSelect } from "../components/common/ModelSelect";
import { currentLlmModel } from "../store/useLlmModelStore";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { Link } from "../router";
import { useAuthStore } from "../store/useAuthStore";
import type { VideoFormat } from "../types";
import { effectLabel, formatFileSize } from "../utils/formatters";
import { clearVideo, loadVideo, saveVideo } from "../utils/videoStore";

// 【수동】 백엔드 VIDEO_MAX_UPLOAD_MB(80) · VIDEO_MAX_SECONDS(20) · VIDEO_MAX_FRAMES(240) 와 맞춤
const MAX_MB = 80;
const MAX_SECONDS = 20;

/** 화면에 보여 주는 결과 (방금 처리했거나 브라우저 보관에서 되살린 것) */
interface Shown {
  blob: Blob;
  format: VideoFormat;
  frames: number;
  held: number;
  prompt: string;
  fileName: string;
  effect?: string;
  intensity?: number;
  /** 서버에도 보관됨(회원) */
  onServer: boolean;
  /** 서버 보관본의 작업 ID — 작업 기록(영상)에서 다시 볼 수 있다 */
  jobId?: string;
  /** 이 브라우저에 보관됨 */
  inBrowser: boolean;
  /** 보관에서 되살린 결과 — 원본 파일이 없어 다시 처리하려면 영상을 다시 올려야 한다 */
  restored: boolean;
}

export function VideoPage() {
  const authStatus = useAuthStore((s) => s.status);
  const userId = useAuthStore((s) => s.user?.id);
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("사람만 남기고 배경 블러");
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [shown, setShown] = useState<Shown | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [playFailed, setPlayFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const owner = userId ?? "guest";

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0]);
      setError(null);
    }
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/mp4": [".mp4"],
      "video/webm": [".webm"],
      "video/quicktime": [".mov"],
      "video/x-msvideo": [".avi"],
      "video/x-matroska": [".mkv"],
    },
    maxSize: MAX_MB * 1024 * 1024,
    multiple: false,
    disabled: running,
  });

  // 로그인 상태가 정해지면 이 브라우저에 보관된 마지막 결과를 되살린다
  useEffect(() => {
    if (authStatus === "loading") return;
    let alive = true;
    void loadVideo(owner).then((saved) => {
      if (!alive || !saved) return;
      setShown((current) =>
        current ?? {
          blob: saved.blob,
          format: saved.format,
          frames: saved.frames,
          held: saved.held,
          prompt: saved.prompt,
          fileName: saved.fileName,
          effect: saved.effect,
          intensity: saved.intensity,
          onServer: false,
          inBrowser: true,
          restored: true,
        },
      );
      setPrompt((current) => (current === "사람만 남기고 배경 블러" ? saved.prompt : current));
    });
    return () => {
      alive = false;
    };
  }, [authStatus, owner]);

  useEffect(() => {
    if (!running) return;
    setElapsed(0);
    const started = Date.now();
    const t = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 500);
    return () => window.clearInterval(t);
  }, [running]);

  // 재생용 object URL — 결과가 바뀌거나 페이지를 떠나면 해제. avi 는 브라우저가 재생하지 못해 만들지 않는다
  useEffect(() => {
    setPlayFailed(false);
    if (!shown || shown.format === "avi" || typeof URL.createObjectURL !== "function") {
      setPreviewUrl(null);
      return;
    }
    const href = URL.createObjectURL(shown.blob);
    setPreviewUrl(href);
    return () => URL.revokeObjectURL(href);
  }, [shown?.blob, shown?.format]); // eslint-disable-line react-hooks/exhaustive-deps

  const run = async () => {
    if (!file) return;
    setRunning(true);
    setError(null);
    try {
      const text = prompt.trim();
      const res = await processVideo(file, text, currentLlmModel());
      const blob = res.kind === "download" ? res.blob : await fetchBlob(res.url);
      const inBrowser = await saveVideo({
        blob,
        format: res.format,
        frames: res.frames,
        held: res.held,
        prompt: text,
        fileName: file.name,
        effect: res.effect,
        intensity: res.intensity,
        owner,
        savedAt: Date.now(),
      });
      setShown({
        blob,
        format: res.format,
        frames: res.frames,
        held: res.held,
        prompt: text,
        fileName: file.name,
        effect: res.effect,
        intensity: res.intensity,
        onServer: res.kind === "saved",
        jobId: res.kind === "saved" ? res.jobId : undefined,
        inBrowser,
        restored: false,
      });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setRunning(false);
    }
  };

  const save = () => {
    if (!shown) return;
    const base = shown.fileName.replace(/\.[^.]+$/, "") || "video";
    saveBlob(shown.blob, `${base}_cutnkeep.${shown.format}`);
  };

  const discard = async () => {
    await clearVideo();
    setShown(null);
  };

  const member = authStatus === "user";
  const retryable = Boolean(file);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="영상"
        title="짧은 영상에도 같은 문장으로"
        description={`영상 한 개(최대 ${MAX_SECONDS}초 · ${MAX_MB}MB)를 프레임마다 처리해요. 대상이 잠깐 안 보이면 직전 장면의 모양을 유지합니다.`}
      />

      <div className="flex gap-3 card p-4 text-xs text-slate-400">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <ul className="space-y-1">
          <li>
            결과는 이 페이지에서 바로 재생되고 <b className="text-slate-300">mp4 파일</b>로 저장할 수 있어요. 마지막 결과 1개는 이 브라우저에도
            보관돼 새로고침해도 다시 볼 수 있어요.
          </li>
          <li>
            {member ? (
              "회원은 결과가 서버에도 24시간 보관돼요."
            ) : (
              <>
                로그인하지 않으면 서버에 <b className="text-slate-300">아무것도 남기지 않아요</b> — 이 브라우저에 보관된 결과가 유일한 사본입니다.{" "}
                <Link to="/login?next=%2Fvideo" className="text-brand-400 hover:text-brand-200">
                  로그인
                </Link>
              </>
            )}
          </li>
          <li>사람이 겹치거나 지나가면 위치·순서로 고른 대상이 프레임마다 바뀔 수 있어요 (추적은 아직 없어요).</li>
        </ul>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="space-y-4">
          <div
            {...getRootProps()}
            className={`group rounded-2xl border-2 border-dashed px-6 py-8 text-center transition ${
              running ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            } ${isDragActive ? "border-brand-400 bg-brand-500/10" : "border-slate-700 bg-slate-900/40 hover:border-brand-500/60 hover:bg-slate-900/70"}`}
          >
            <input {...getInputProps()} />
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 ring-1 ring-inset ring-brand-500/25 transition group-hover:scale-105">
              <Clapperboard className="h-6 w-6 text-brand-400" />
            </span>
            {file ? (
              <div className="mt-2 flex items-center justify-center gap-2 text-sm text-slate-100">
                <span className="truncate">{file.name}</span>
                <span className="text-xs text-slate-500">{formatFileSize(file.size)}</span>
                {!running && (
                  <button
                    type="button"
                    aria-label="영상 빼기"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="text-slate-500 hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            ) : (
              <>
                <p className="mt-2 text-sm text-slate-100">영상을 드래그하거나 클릭</p>
                <p className="text-xs text-slate-500">mp4 · webm · mov · avi · mkv · 최대 {MAX_MB}MB</p>
              </>
            )}
          </div>

          <label className="block space-y-2">
            <span className="text-sm text-slate-200">영상에 적용할 문장</span>
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={running}
              className="field"
            />
            <span className="block text-xs text-slate-500">블러를 더 세게: "배경 블러 강도 60" 처럼 숫자를 적어 보세요.</span>
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => void run()} disabled={running || !file || !prompt.trim()}>
              {running ? "처리 중…" : shown ? (
                <>
                  <RotateCcw className="h-4 w-4" /> 다시 처리
                </>
              ) : (
                "영상 처리 시작"
              )}
            </Button>
            <ModelSelect disabled={running} />
          </div>
          {shown && !file && !running && (
            <p className="text-xs text-slate-500">다시 처리하려면 원본 영상을 올려 주세요 (결과만 이 브라우저에 보관돼요).</p>
          )}
        </section>

        <section className="space-y-4" aria-live="polite">
          {running && (
            <div className="flex items-center gap-3 rounded-xl border border-brand-700/40 bg-brand-900/20 px-3 py-2 text-sm text-brand-100">
              <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
              <span className="flex-1">프레임마다 대상을 찾고 있어요 — 영상 길이에 따라 몇 분 걸릴 수 있어요</span>
              <span className="tabular-nums text-xs text-brand-100/70">{elapsed}s</span>
            </div>
          )}
          {shown && (
            <div className="space-y-3 card p-4 text-sm">
              <p className="font-semibold text-white">{shown.restored ? "이 브라우저에 보관된 마지막 결과" : "처리가 끝났어요"}</p>
              <p className="text-xs text-slate-400">
                {shown.frames}프레임 처리 · 대상이 없어 직전 모양을 유지한 프레임 {shown.held}개
                {shown.onServer ? " · 서버에 보관됨 (24시간)" : " · 서버에 저장되지 않았어요"}
              </p>
              {shown.onServer && shown.jobId && (
                <Link to={`/jobs/${shown.jobId}`} className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-200">
                  작업 기록에서 보기 →
                </Link>
              )}
              {shown.effect && (
                <p className="text-xs text-slate-300" data-testid="video-applied">
                  적용된 효과: <b>{effectLabel(shown.effect)}</b>
                  {shown.effect === "blur" && shown.intensity !== undefined && ` · 강도 ${shown.intensity}`}
                  <span className="text-slate-500"> — 문장 “{shown.prompt}”</span>
                </p>
              )}
              {shown.effect !== undefined && shown.effect !== "blur" && /블러|흐리|blur/i.test(shown.prompt) && (
                <p className="text-xs text-amber-200/80">
                  문장에 블러가 있는데 “{effectLabel(shown.effect)}”로 해석됐어요. “배경 블러”처럼 효과를 분명히 적어 다시 처리해 보세요.
                </p>
              )}
              {previewUrl && !playFailed && (
                <video
                  src={previewUrl}
                  controls
                  loop
                  playsInline
                  aria-label="처리 결과 영상"
                  onError={() => setPlayFailed(true)}
                  className="w-full rounded-xl border border-slate-800 bg-black"
                />
              )}
              {(shown.format === "avi" || playFailed) && (
                <p className="text-xs text-amber-200/80">
                  {shown.format === "avi"
                    ? "서버에 ffmpeg 가 없어 avi 로 만들었어요 — 브라우저에서는 재생되지 않으니 내려받아 열어 주세요."
                    : "이 브라우저에서 재생되지 않아요 — 저장해서 영상 플레이어로 열어 주세요."}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={save}>
                  <Download className="h-4 w-4" /> 결과 저장 ({shown.format})
                </Button>
                <button
                  type="button"
                  onClick={() => void discard()}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300 hover:border-slate-500"
                >
                  <Trash2 className="h-3.5 w-3.5" /> 보관된 결과 지우기
                </button>
                {shown.inBrowser && (
                  <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                    <HardDrive className="h-3.5 w-3.5" /> 이 브라우저에 보관됨
                  </span>
                )}
              </div>
              {!shown.inBrowser && !shown.restored && (
                <p className="text-xs text-slate-500">브라우저 저장소를 쓸 수 없어(시크릿 창 등) 이 결과는 새로고침하면 사라져요. 바로 저장해 주세요.</p>
              )}
              {retryable && <p className="text-xs text-slate-500">결과가 마음에 들지 않으면 문장을 고치고 “다시 처리”를 눌러 주세요.</p>}
            </div>
          )}
          {!running && !shown && !error && (
            <p className="rounded-2xl border border-dashed border-slate-800 py-16 text-center text-sm text-slate-500">
              영상을 올리고 처리하면 결과를 바로 재생하고 내려받을 수 있어요.
            </p>
          )}
          {error && (
            <p className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">{error}</p>
          )}
        </section>
      </div>
    </div>
  );
}

/**
 * 영상 (/video) — 짧은 영상 한 개에 같은 문장을 프레임마다 적용.
 *
 * 비로그인도 쓸 수 있지만 서버에 아무것도 남기지 않으므로 결과를 바로 내려받아야 한다.
 * 회원은 서버에 보관된 결과를 24시간 동안 다시 받을 수 있다.
 * 결과는 webm(VP8)이라 페이지에서 바로 재생한다. 서버에 VP8 인코더가 없으면 avi(다운로드 전용)로 온다.
 * 처리는 동기라 길게 기다린다 (프레임마다 세그).
 */
import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Clapperboard, Download, Info, Loader2, X } from "lucide-react";
import { errorMessage, fetchBlob, processVideo, saveBlob } from "../api/client";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { Link } from "../router";
import { useAuthStore } from "../store/useAuthStore";
import type { VideoResult } from "../types";
import { formatFileSize } from "../utils/formatters";

// 【수동】 백엔드 VIDEO_MAX_UPLOAD_MB(80) · VIDEO_MAX_SECONDS(20) · VIDEO_MAX_FRAMES(240) 와 맞춤
const MAX_MB = 80;
const MAX_SECONDS = 20;

export function VideoPage() {
  const authStatus = useAuthStore((s) => s.status);
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("사람만 남기고 배경 블러");
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  // 재생·저장에 쓰는 결과 Blob (회원 보관본은 인증 요청으로 받아 온다)
  const [blob, setBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0]);
      setResult(null);
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

  useEffect(() => {
    if (!running) return;
    setElapsed(0);
    const started = Date.now();
    const t = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 500);
    return () => window.clearInterval(t);
  }, [running]);

  useEffect(() => {
    setBlob(null);
    if (!result) return;
    if (result.kind === "download") {
      setBlob(result.blob);
      return;
    }
    let alive = true;
    fetchBlob(result.url)
      .then((b) => alive && setBlob(b))
      .catch((err) => alive && setError(errorMessage(err)));
    return () => {
      alive = false;
    };
  }, [result]);

  // webm 만 브라우저가 재생한다. object URL 은 바뀌거나 페이지를 떠날 때 해제
  useEffect(() => {
    if (!blob || result?.format !== "webm" || typeof URL.createObjectURL !== "function") {
      setPreviewUrl(null);
      return;
    }
    const href = URL.createObjectURL(blob);
    setPreviewUrl(href);
    return () => URL.revokeObjectURL(href);
  }, [blob, result?.format]);

  const run = async () => {
    if (!file) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      setResult(await processVideo(file, prompt.trim()));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setRunning(false);
    }
  };

  const save = () => {
    if (!result || !blob) return;
    saveBlob(blob, `cutnkeep_video.${result.format}`);
  };

  const member = authStatus === "user";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="영상"
        title="짧은 영상에도 같은 문장으로"
        description={`영상 한 개(최대 ${MAX_SECONDS}초 · ${MAX_MB}MB)를 프레임마다 처리해요. 대상이 잠깐 안 보이면 직전 장면의 모양을 유지합니다.`}
      />

      <div className="flex gap-3 rounded-2xl border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-400">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <ul className="space-y-1">
          <li>
            결과는 이 페이지에서 바로 재생되고 <b className="text-slate-300">webm 파일</b>로 저장할 수 있어요.
          </li>
          <li>
            {member ? (
              "회원은 결과가 서버에 24시간 보관돼 그 안에는 다시 받을 수 있어요."
            ) : (
              <>
                로그인하지 않으면 서버에 <b className="text-slate-300">아무것도 남기지 않아요</b> — 처리가 끝나면 바로 내려받아야 합니다.{" "}
                <Link to="/login?next=%2Fvideo" className="text-brand-500 hover:text-brand-100">
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
            className={`rounded-2xl border-2 border-dashed p-6 text-center transition ${
              running ? "cursor-not-allowed opacity-60" : "cursor-pointer"
            } ${isDragActive ? "border-brand-500 bg-brand-500/10" : "border-slate-700 bg-slate-900/60 hover:border-slate-500"}`}
          >
            <input {...getInputProps()} />
            <Clapperboard className="mx-auto h-8 w-8 text-slate-400" />
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
                      setResult(null);
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
              className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-brand-500"
            />
          </label>
          <Button onClick={() => void run()} disabled={running || !file || !prompt.trim()}>
            {running ? "처리 중…" : "영상 처리 시작"}
          </Button>
        </section>

        <section className="space-y-4" aria-live="polite">
          {running && (
            <div className="flex items-center gap-3 rounded-xl border border-brand-700/40 bg-brand-900/20 px-3 py-2 text-sm text-brand-100">
              <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
              <span className="flex-1">프레임마다 대상을 찾고 있어요 — 영상 길이에 따라 몇 분 걸릴 수 있어요</span>
              <span className="tabular-nums text-xs text-brand-100/70">{elapsed}s</span>
            </div>
          )}
          {result && (
            <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm">
              <p className="font-semibold text-white">처리가 끝났어요</p>
              <p className="text-xs text-slate-400">
                {result.frames}프레임 처리 · 대상이 없어 직전 모양을 유지한 프레임 {result.held}개
                {result.kind === "saved" ? " · 서버에 보관됨 (24시간)" : " · 서버에 저장되지 않았어요"}
              </p>
              {previewUrl && (
                <video
                  src={previewUrl}
                  controls
                  loop
                  playsInline
                  aria-label="처리 결과 영상"
                  className="w-full rounded-xl border border-slate-800 bg-black"
                />
              )}
              {result.format === "avi" && (
                <p className="text-xs text-amber-200/80">
                  서버에 webm 인코더가 없어 avi 로 만들었어요 — 브라우저에서는 재생되지 않으니 내려받아 열어 주세요.
                </p>
              )}
              <Button onClick={save} disabled={!blob}>
                <Download className="h-4 w-4" /> 결과 저장 ({result.format})
              </Button>
            </div>
          )}
          {!running && !result && !error && (
            <p className="rounded-2xl border border-dashed border-slate-800 py-16 text-center text-sm text-slate-500">
              영상을 올리고 처리하면 결과를 내려받을 수 있어요.
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

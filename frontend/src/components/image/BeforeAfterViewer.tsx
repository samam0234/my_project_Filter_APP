/**
 * 처리 결과 Before / After 비교 뷰 (작업실 · 작업 상세 공용 — 사진 · GIF · 영상).
 *
 * - 해석 결과(ParsedPromptView)를 함께 보여줘 "왜 이렇게 됐는지" 알 수 있게 한다
 * - failed 면 서버 message(예: "요청한 대상(bus)을 찾지 못했습니다. 감지된 대상: …")를 강조
 * - after 는 투명 PNG/GIF 를 위해 체크무늬 배경
 * - media="video" 면 <video> 로 재생 (작업 기록의 영상)
 */
import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { buttonClass } from "../common/Button";
import type { ParsedPrompt } from "../../types";
import { formatScore } from "../../utils/formatters";
import { StatusBadge } from "../common/StatusBadge";
import { ParsedPromptView } from "../prompt/ParsedPromptView";
import { ResultImage } from "./ResultImage";

interface Props {
  status: string;
  /** 사진만 품질 점수가 있다 — null 이면 숨김 (영상 · GIF) */
  qualityScore?: number | null;
  beforeUrl?: string | null;
  afterUrl?: string | null;
  parsedPrompt?: ParsedPrompt | null;
  message?: string | null;
  jobId?: string;
  media?: "image" | "video";
  /** 결과 저장 파일 확장자 (기본: 배경 제거면 .png, 아니면 .jpg) */
  fileExt?: string;
  /** 상태가 ok 여도 보여 줄 안내 (예: GIF 프레임을 일부만 처리) */
  note?: string | null;
}

function ResultVideo({ src, label }: { src?: string | null; label: string }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  if (!src || failed) {
    return (
      <div className="flex aspect-video items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/60 px-4 text-center text-xs text-slate-500">
        {src
          ? "이 브라우저에서 재생할 수 없는 형식이거나 보관 기간이 지났어요"
          : "영상을 불러오지 못했어요 (보관 기간이 지났을 수 있어요)"}
      </div>
    );
  }
  return (
    <video
      src={src}
      controls
      playsInline
      muted
      loop
      preload="metadata"
      onError={() => setFailed(true)}
      aria-label={label}
      className="w-full rounded-xl border border-slate-800/80 bg-black"
    />
  );
}

export function BeforeAfterViewer({
  status,
  qualityScore,
  beforeUrl,
  afterUrl,
  parsedPrompt,
  message,
  jobId,
  media = "image",
  fileExt,
  note,
}: Props) {
  const transparent = parsedPrompt?.effect === "remove_bg";
  const ext = fileExt ?? (transparent ? ".png" : ".jpg");
  return (
    <section className="card animate-fade-up space-y-4 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-white">결과</h2>
          <StatusBadge status={status} />
          {qualityScore != null && <span className="text-xs text-slate-500">품질 {formatScore(qualityScore)}</span>}
        </div>
        {afterUrl && (
          <a
            href={afterUrl}
            download={jobId ? `cutnkeep_${jobId}${ext}` : undefined}
            className={buttonClass("primary", "sm")}
          >
            <Download className="h-3.5 w-3.5" /> 결과 저장
          </a>
        )}
      </div>

      <div className="space-y-2 rounded-xl bg-slate-950/50 p-3 ring-1 ring-inset ring-slate-800">
        <p className="text-xs font-medium text-slate-400">이렇게 이해했어요</p>
        <ParsedPromptView parsed={parsedPrompt} />
      </div>

      {((message && status !== "ok") || note) && (
        <p className="rounded-lg border border-amber-800/40 bg-amber-950/30 px-3 py-2 text-xs leading-relaxed text-amber-200">
          {status !== "ok" ? message : note}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <figure className="space-y-2">
          <figcaption className="text-xs font-medium text-slate-400">원본</figcaption>
          {media === "video" ? (
            <ResultVideo src={beforeUrl} label="원본 영상" />
          ) : (
            <ResultImage src={beforeUrl} alt="원본 이미지" />
          )}
        </figure>
        <figure className="space-y-2">
          <figcaption className="text-xs font-medium text-brand-300">결과</figcaption>
          {media === "video" ? (
            <ResultVideo src={afterUrl} label="결과 영상" />
          ) : (
            <ResultImage src={afterUrl} alt="처리 결과" checker={transparent} />
          )}
        </figure>
      </div>
    </section>
  );
}

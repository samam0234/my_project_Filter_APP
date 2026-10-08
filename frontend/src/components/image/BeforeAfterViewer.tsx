/**
 * 처리 결과 Before / After 비교 뷰 (작업실 · 작업 상세 공용).
 *
 * - 해석 결과(ParsedPromptView)를 함께 보여줘 "왜 이렇게 됐는지" 알 수 있게 한다
 * - failed 면 서버 message(예: "요청한 대상(bus)을 찾지 못했습니다. 감지된 대상: …")를 강조
 * - after 는 투명 PNG 를 위해 체크무늬 배경
 */
import { Download } from "lucide-react";
import { buttonClass } from "../common/Button";
import type { ParsedPrompt } from "../../types";
import { formatScore } from "../../utils/formatters";
import { StatusBadge } from "../common/StatusBadge";
import { ParsedPromptView } from "../prompt/ParsedPromptView";
import { ResultImage } from "./ResultImage";

interface Props {
  status: string;
  qualityScore: number;
  beforeUrl?: string | null;
  afterUrl?: string | null;
  parsedPrompt?: ParsedPrompt | null;
  message?: string | null;
  jobId?: string;
}

export function BeforeAfterViewer({
  status,
  qualityScore,
  beforeUrl,
  afterUrl,
  parsedPrompt,
  message,
  jobId,
}: Props) {
  const transparent = parsedPrompt?.effect === "remove_bg";
  return (
    <section className="card animate-fade-up space-y-4 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-white">결과</h2>
          <StatusBadge status={status} />
          <span className="text-xs text-slate-500">품질 {formatScore(qualityScore)}</span>
        </div>
        {afterUrl && (
          <a
            href={afterUrl}
            download={jobId ? `cutnkeep_${jobId}${transparent ? ".png" : ".jpg"}` : undefined}
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

      {message && status !== "ok" && (
        <p className="rounded-lg border border-amber-800/40 bg-amber-950/30 px-3 py-2 text-xs leading-relaxed text-amber-200">
          {message}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <figure className="space-y-2">
          <figcaption className="text-xs font-medium text-slate-400">원본</figcaption>
          <ResultImage src={beforeUrl} alt="원본 이미지" />
        </figure>
        <figure className="space-y-2">
          <figcaption className="text-xs font-medium text-brand-300">결과</figcaption>
          <ResultImage src={afterUrl} alt="처리 결과" checker={transparent} />
        </figure>
      </div>
    </section>
  );
}

/**
 * 작업 카드 — 결과 썸네일 · 종류(사진·영상·GIF) · 프롬프트 · 상태 · 시간. 누르면 작업 상세로.
 * 썸네일: 서버 thumb_url (영상은 첫 프레임 jpg, GIF 는 움직이는 결과) → 없으면 결과 → 원본.
 */
import { Clapperboard, Film } from "lucide-react";
import { resolveAssetUrl } from "../../api/client";
import { Link } from "../../router";
import type { JobResponse } from "../../types";
import { formatRelative } from "../../utils/formatters";
import { StatusBadge } from "../common/StatusBadge";
import { ResultImage } from "../image/ResultImage";

const KIND_BADGE = {
  video: { label: "영상", icon: Clapperboard },
  gif: { label: "GIF", icon: Film },
} as const;

export function JobCard({ job }: { job: JobResponse }) {
  const kind = job.kind ?? "image";
  const thumb = resolveAssetUrl(job.thumb_url ?? job.after_url ?? job.before_url);
  const badge = kind === "image" ? null : KIND_BADGE[kind];
  return (
    <Link
      to={`/jobs/${job.job_id}`}
      className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:border-brand-600/50 hover:bg-slate-900/80"
    >
      <div className="relative p-2">
        <ResultImage
          src={thumb}
          alt={job.prompt}
          checker={kind !== "video" && job.parsed_prompt?.effect === "remove_bg"}
          className="aspect-[4/3] object-cover"
        />
        {badge && (
          <span className="absolute left-4 top-4 inline-flex items-center gap-1 rounded-md bg-slate-950/80 px-1.5 py-0.5 text-[11px] font-medium text-slate-100 ring-1 ring-slate-700 backdrop-blur">
            <badge.icon className="h-3 w-3 text-brand-300" /> {badge.label}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 px-3 pb-3">
        <p className="line-clamp-2 text-sm text-slate-200 group-hover:text-white">{job.prompt}</p>
        <div className="mt-auto flex items-center justify-between text-xs text-slate-500">
          <StatusBadge status={job.status} />
          <span>{formatRelative(job.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

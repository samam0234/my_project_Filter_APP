/**
 * 작업 카드 — 결과 썸네일 · 프롬프트 · 상태 · 시간. 누르면 작업 상세로.
 */
import { resolveAssetUrl } from "../../api/client";
import { Link } from "../../router";
import type { JobResponse } from "../../types";
import { formatRelative } from "../../utils/formatters";
import { StatusBadge } from "../common/StatusBadge";
import { ResultImage } from "../image/ResultImage";

export function JobCard({ job }: { job: JobResponse }) {
  const thumb = resolveAssetUrl(job.after_url ?? job.before_url);
  return (
    <Link
      to={`/jobs/${job.job_id}`}
      className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:border-brand-600/50 hover:bg-slate-900/80"
    >
      <div className="p-2">
        <ResultImage
          src={thumb}
          alt={job.prompt}
          checker={job.parsed_prompt?.effect === "remove_bg"}
          className="aspect-[4/3] object-cover"
        />
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

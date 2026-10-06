/**
 * 작업 상세 (/jobs/:id) — 결과 · 해석 · 메타 · 평가/정답 알려주기 · 다시 작업.
 */
import { ArrowLeft, Copy, Repeat } from "lucide-react";
import { useState, type ReactNode } from "react";
import { resolveAssetUrl } from "../api/client";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { ErrorBlock, LoadingBlock } from "../components/common/States";
import { FeedbackPanel } from "../components/feedback/FeedbackPanel";
import { BeforeAfterViewer } from "../components/image/BeforeAfterViewer";
import { RequireLogin } from "../components/auth/RequireLogin";
import { useJob } from "../hooks/useApi";
import { Link, navigate } from "../router";
import { useAppStore } from "../store/useAppStore";
import { formatDateTime } from "../utils/formatters";

export function JobDetailPage({ jobId }: { jobId: string }) {
  return (
    <RequireLogin title="작업 상세는 로그인 회원 전용이에요" reason="내 계정으로 처리한 작업만 볼 수 있어요.">
      <JobDetail jobId={jobId} />
    </RequireLogin>
  );
}

function JobDetail({ jobId }: { jobId: string }) {
  const { data: job, error, loading, reload } = useJob(jobId);
  const setPrompt = useAppStore((s) => s.setPrompt);
  const [copied, setCopied] = useState(false);

  if (loading && !job) return <LoadingBlock />;
  if (error || !job) {
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorBlock
          message={
            error?.includes("찾을 수 없") || error?.includes("없음")
              ? "작업을 찾을 수 없어요. 삭제되었거나 다른 계정의 작업입니다."
              : error ?? "작업을 불러오지 못했어요."
          }
          onRetry={reload}
        />
      </div>
    );
  }

  const retry = () => {
    setPrompt(job.prompt);
    navigate("/studio");
  };

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(job.parsed_prompt, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* 클립보드 권한 없음 — 무시 */
    }
  };

  return (
    <div className="space-y-6">
      <BackLink />
      <PageHeader
        eyebrow="작업 상세"
        title={job.prompt}
        description={formatDateTime(job.created_at)}
        actions={
          <Button variant="secondary" onClick={retry} title="같은 문장이 작업실에 채워집니다 (이미지는 다시 올려야 해요)">
            <Repeat className="h-4 w-4" /> 이 문장으로 다시 작업
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,8fr)_minmax(0,4fr)]">
        <div className="space-y-4">
          <BeforeAfterViewer
            jobId={job.job_id}
            status={job.status}
            qualityScore={job.quality_score}
            beforeUrl={resolveAssetUrl(job.before_url)}
            afterUrl={resolveAssetUrl(job.after_url)}
            parsedPrompt={job.parsed_prompt}
            message={job.message}
          />
          <FeedbackPanel key={job.job_id} jobId={job.job_id} parsed={job.parsed_prompt} />
        </div>

        <aside className="space-y-4">
          <dl className="space-y-2 rounded-2xl border border-slate-800 bg-slate-900/40 p-4 text-sm">
            <Row label="작업 ID">
              <code className="break-all text-xs text-slate-300">{job.job_id}</code>
            </Row>
            <Row label="세그 엔진">{job.backend ?? "-"}</Row>
            <Row label="서버 메시지">{job.message ?? "-"}</Row>
            <Row label="피드백">{job.feedback_saved ? "저장됨 (학습 데이터 후보)" : "없음"}</Row>
          </dl>
          <div className="space-y-2 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-400">해석 JSON</p>
              <button
                type="button"
                onClick={() => void copyJson()}
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white"
              >
                <Copy className="h-3.5 w-3.5" /> {copied ? "복사됨" : "복사"}
              </button>
            </div>
            <pre className="max-h-72 overflow-auto text-[11px] text-slate-400">
              {JSON.stringify(job.parsed_prompt, null, 2)}
            </pre>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex gap-3">
      <dt className="w-28 shrink-0 text-slate-500">{label}</dt>
      <dd className="min-w-0 flex-1 text-slate-200">{children}</dd>
    </div>
  );
}

function BackLink() {
  return (
    <Link to="/history" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white">
      <ArrowLeft className="h-4 w-4" /> 작업 기록
    </Link>
  );
}

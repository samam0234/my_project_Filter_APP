/**
 * 작업실 (/studio) — 카테고리(사진 · GIF · 영상) · 업로드 · 프롬프트 · 처리 · 결과 · 평가.
 *
 * 카테고리는 URL 쿼리 ?type=gif 로 남겨 새로고침·링크(작업 기록의 "다시 작업")에서도 유지한다.
 * 영상은 처리 방식·보관이 달라 별도 페이지(/video)로 보낸다.
 * 왼쪽: 입력 (파일 · 문장 · 버튼 · 진행 상태) / 오른쪽: 결과 (해석 칩 · Before/After · 평가/정답 알려주기)
 * 사진 상태는 useAppStore 에 있어 다른 페이지에 다녀와도 유지된다.
 */
import { Clapperboard, ExternalLink, Film, ImageIcon, RotateCcw, Wand2 } from "lucide-react";
import { useMemo } from "react";
import { GifWorkspace } from "../components/gif/GifWorkspace";
import { Button } from "../components/common/Button";
import { Step } from "../components/common/Step";
import { PageHeader } from "../components/common/PageHeader";
import { FeedbackPanel } from "../components/feedback/FeedbackPanel";
import { BeforeAfterViewer } from "../components/image/BeforeAfterViewer";
import { ImageUploader } from "../components/image/ImageUploader";
import { ProcessingStatus } from "../components/image/ProcessingStatus";
import { PromptInput } from "../components/prompt/PromptInput";
import { useImageProcessing } from "../hooks/useImageProcessing";
import { Link, navigate, useSearch } from "../router";
import { useAppStore } from "../store/useAppStore";
import { useAuthStore } from "../store/useAuthStore";

type StudioType = "photo" | "gif";

const CATEGORIES = [
  { id: "photo", label: "사진", icon: ImageIcon, hint: "JPEG · PNG · WebP" },
  { id: "gif", label: "GIF", icon: Film, hint: "움직이는 GIF" },
] as const;

export function StudioPage() {
  const search = useSearch();
  const type: StudioType = useMemo(() => (new URLSearchParams(search).get("type") === "gif" ? "gif" : "photo"), [search]);
  const select = (next: StudioType) => navigate(next === "gif" ? "/studio?type=gif" : "/studio", { replace: true });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="작업실"
        title={type === "gif" ? "GIF 배경 제거 · 대상 편집" : "이미지 배경 제거 · 대상 편집"}
        description={
          type === "gif"
            ? "움직이는 GIF 를 올리고 원하는 것을 한 문장으로 적어 주세요. 모든 프레임에 같은 요청을 적용해요."
            : "사진을 올리고 원하는 것을 한 문장으로 적어 주세요."
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <div role="tablist" aria-label="작업 종류" className="inline-flex gap-1 rounded-xl border border-slate-800 bg-slate-900/50 p-1">
          {CATEGORIES.map(({ id, label, icon: Icon, hint }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={type === id}
              title={hint}
              onClick={() => select(id)}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
                type === id ? "bg-slate-800 text-white shadow-card" : "text-slate-400 hover:text-slate-100"
              }`}
            >
              <Icon className={`h-4 w-4 ${type === id ? "text-brand-400" : ""}`} />
              {label}
            </button>
          ))}
        </div>
        <Link
          to="/video"
          className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-100"
        >
          <Clapperboard className="h-4 w-4" /> 영상은 여기에서 →
        </Link>
      </div>

      {type === "gif" ? <GifWorkspace /> : <PhotoWorkspace />}
    </div>
  );
}

function PhotoWorkspace() {
  const { process, isProcessing } = useImageProcessing();
  const reset = useAppStore((s) => s.reset);
  const file = useAppStore((s) => s.file);
  const prompt = useAppStore((s) => s.prompt);
  const result = useAppStore((s) => s.result);
  const guest = useAuthStore((s) => s.status === "guest");
  const canRun = Boolean(file && prompt.trim()) && !isProcessing;

  return (
    <div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="card space-y-7 p-5 sm:p-6">
          <Step n={1} title="사진 올리기" done={Boolean(file)}>
            <ImageUploader />
          </Step>
          <Step n={2} title="무엇을 남기거나 지울까요?" done={Boolean(prompt.trim())}>
            <PromptInput onSubmit={() => canRun && void process()} />
          </Step>
          <Step n={3} title="처리하기">
            <div className="flex flex-wrap gap-2">
              <Button size="lg" onClick={() => void process()} disabled={!canRun} className="flex-1 sm:flex-none">
                <Wand2 className="h-4 w-4" /> 처리 시작
              </Button>
              <Button variant="ghost" size="lg" onClick={() => reset()} disabled={isProcessing}>
                <RotateCcw className="h-4 w-4" /> 초기화
              </Button>
            </div>
            {!canRun && !isProcessing && (
              <p className="text-xs text-slate-500">
                {!file ? "먼저 사진을 올려 주세요." : "문장을 적으면 시작할 수 있어요."}
              </p>
            )}
            <ProcessingStatus />
          </Step>
          {guest && (
            <p className="border-t border-slate-800 pt-4 text-xs leading-relaxed text-slate-500">
              <Link to="/login?next=%2Fstudio" className="text-brand-400 hover:text-brand-200">
                로그인
              </Link>
              하면 처리한 작업이 작업 기록에 저장됩니다. 로그인하지 않으면 결과를 저장하지 않고 다운로드만 할 수 있어요.
            </p>
          )}
        </div>

        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          {result ? (
            <>
              <BeforeAfterViewer
                jobId={result.jobId}
                status={result.status}
                qualityScore={result.qualityScore}
                beforeUrl={result.beforeUrl}
                afterUrl={result.afterUrl}
                parsedPrompt={result.parsedPrompt}
                message={result.message}
              />
              {result.saved ? (
                <>
                  <FeedbackPanel key={result.jobId} jobId={result.jobId} parsed={result.parsedPrompt} />
                  <Link
                    to={`/jobs/${result.jobId}`}
                    className="inline-flex items-center gap-1.5 text-sm text-brand-400 hover:text-brand-200"
                  >
                    작업 상세 보기 <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </>
              ) : (
                <div className="space-y-1 rounded-2xl border border-amber-800/40 bg-amber-950/20 p-4 text-sm text-amber-100/90">
                  <p className="font-medium">이 결과는 저장되지 않아요</p>
                  <p className="text-xs text-amber-100/70">
                    로그인하지 않은 작업은 서버에 남기지 않습니다. 필요하면 지금 <b>결과 저장</b>으로 내려받으세요 —
                    페이지를 새로고침하면 사라집니다.{" "}
                    <Link to="/login?next=%2Fstudio" className="text-brand-400 hover:text-brand-200">
                      로그인
                    </Link>
                    하면 작업 기록 · 피드백 · 배치를 쓸 수 있어요.
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 rounded-2xl lg:min-h-[420px] border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center text-sm text-slate-500">
              {isProcessing ? (
                <>
                  <span className="relative flex h-14 w-14 items-center justify-center">
                    <span className="absolute inset-0 animate-ping rounded-2xl bg-brand-500/20" />
                    <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/15 ring-1 ring-inset ring-brand-500/40">
                      <Wand2 className="h-6 w-6 text-brand-300" />
                    </span>
                  </span>
                  <p className="text-slate-300">결과를 만드는 중이에요</p>
                </>
              ) : (
                <>
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/70 ring-1 ring-inset ring-slate-700/60">
                    <ImageIcon className="h-6 w-6 text-slate-400" />
                  </span>
                  <p className="text-slate-300">처리 결과가 여기에 표시됩니다.</p>
                </>
              )}
              <p className="max-w-xs text-xs leading-relaxed">
                처음 요청은 모델을 불러오느라 30초 이상 걸릴 수 있어요.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

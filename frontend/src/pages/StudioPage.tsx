/**
 * 작업실 (/studio) — 이미지 업로드 · 프롬프트 · 처리 · 결과 · 평가.
 *
 * 왼쪽: 입력 (이미지 · 문장 · 버튼 · 진행 상태)
 * 오른쪽: 결과 (해석 칩 · Before/After · 평가/정답 알려주기)
 * 상태는 useAppStore 에 있어 다른 페이지에 다녀와도 유지된다.
 */
import { ExternalLink, RotateCcw, Wand2 } from "lucide-react";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { FeedbackPanel } from "../components/feedback/FeedbackPanel";
import { BeforeAfterViewer } from "../components/image/BeforeAfterViewer";
import { ImageUploader } from "../components/image/ImageUploader";
import { ProcessingStatus } from "../components/image/ProcessingStatus";
import { PromptInput } from "../components/prompt/PromptInput";
import { useImageProcessing } from "../hooks/useImageProcessing";
import { Link } from "../router";
import { useAppStore } from "../store/useAppStore";
import { useAuthStore } from "../store/useAuthStore";

export function StudioPage() {
  const { process, isProcessing } = useImageProcessing();
  const reset = useAppStore((s) => s.reset);
  const file = useAppStore((s) => s.file);
  const prompt = useAppStore((s) => s.prompt);
  const result = useAppStore((s) => s.result);
  const guest = useAuthStore((s) => s.status === "guest");
  const canRun = Boolean(file && prompt.trim()) && !isProcessing;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="작업실"
        title="이미지 배경 제거 · 대상 편집"
        description="사진을 올리고 원하는 것을 한 문장으로 적어 주세요."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="space-y-5">
          <ImageUploader />
          <PromptInput onSubmit={() => canRun && void process()} />
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => void process()} disabled={!canRun}>
              <Wand2 className="h-4 w-4" /> 처리 시작
            </Button>
            <Button variant="ghost" onClick={() => reset()} disabled={isProcessing}>
              <RotateCcw className="h-4 w-4" /> 초기화
            </Button>
          </div>
          <ProcessingStatus />
          {guest && (
            <p className="text-xs text-slate-500">
              <Link to="/login?next=%2Fstudio" className="text-brand-500 hover:text-brand-100">
                로그인
              </Link>
              하면 처리한 작업이 작업 기록에 저장됩니다. 로그인하지 않으면 결과를 저장하지 않고 다운로드만 할 수 있어요.
            </p>
          )}
        </div>

        <div className="space-y-4">
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
                    className="inline-flex items-center gap-1.5 text-sm text-brand-500 hover:text-brand-100"
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
                    <Link to="/login?next=%2Fstudio" className="text-brand-500 hover:text-brand-100">
                      로그인
                    </Link>
                    하면 작업 기록 · 피드백 · 배치를 쓸 수 있어요.
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full min-h-[320px] flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-800 p-8 text-center text-sm text-slate-500">
              <Wand2 className="h-6 w-6" />
              <p>처리 결과가 여기에 표시됩니다.</p>
              <p className="text-xs">
                처음 요청은 모델을 불러오느라 30초 이상 걸릴 수 있어요.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

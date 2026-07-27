import { Scissors } from "lucide-react";
import { Button } from "./components/common/Button";
import { ImageUploader } from "./components/image/ImageUploader";
import { BeforeAfterViewer } from "./components/image/BeforeAfterViewer";
import { ProcessingStatus } from "./components/image/ProcessingStatus";
import { PromptInput } from "./components/prompt/PromptInput";
import { FeedbackButtons } from "./components/feedback/FeedbackButtons";
import { BatchUploader } from "./components/batch/BatchUploader";
import { useImageProcessing } from "./hooks/useImageProcessing";
import { useAppStore } from "./store/useAppStore";

export default function App() {
  const { process, isProcessing } = useImageProcessing();
  const reset = useAppStore((s) => s.reset);
  const file = useAppStore((s) => s.file);

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-4 py-10">
      <header className="space-y-2">
        <div className="flex items-center gap-2 text-brand-500">
          <Scissors className="h-6 w-6" />
          <span className="text-xs font-semibold uppercase tracking-widest">
            Cut & Keep
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">
          컷앤킵 — 프롬프트로 원하는 것만 남기기
        </h1>
        <p className="text-sm text-slate-400">
          자연어로 대상을 지정하면 배경을 제거하고 선택 효과(블러/크롭)를
          적용합니다. Phase 1 MVP 스켈레톤.
        </p>
      </header>

      <main className="flex flex-col gap-5">
        <ImageUploader />
        <PromptInput />
        <ProcessingStatus />

        <div className="flex flex-wrap gap-3">
          <Button onClick={() => process()} disabled={isProcessing || !file}>
            처리 시작
          </Button>
          <Button variant="ghost" onClick={() => reset()} disabled={isProcessing}>
            초기화
          </Button>
        </div>

        <BeforeAfterViewer />
        <FeedbackButtons />
        <BatchUploader />
      </main>

      <footer className="mt-auto border-t border-slate-800 pt-4 text-xs text-slate-500">
        docs/plan 로직 구조 기반 · YOLO-seg + LangGraph + OpenCV
      </footer>
    </div>
  );
}

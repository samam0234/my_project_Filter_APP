/**
 * 사용자 앱 루트 화면 (Vite :5173).
 *
 * 레이아웃 순서:
 *  1) 이미지 업로드
 *  2) 프롬프트 입력
 *  3) 처리 상태
 *  4) 처리 시작 / 초기화
 *  5) Before/After · 피드백 · 배치(스캐폴드)
 *
 * 상태: useAppStore (Zustand)
 * API 호출: useImageProcessing → POST /api/v1/upload
 */
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
  // 업로드·처리 훅 (로딩 플래그 포함)
  const { process, isProcessing } = useImageProcessing();
  // 전역 초기화 (파일/미리보기/결과 클리어)
  const reset = useAppStore((s) => s.reset);
  const file = useAppStore((s) => s.file);

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-4 py-10">
      {/* --- 헤더: 브랜드 + Phase 1 안내 --- */}
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
        {/* 파일 선택 (드래그앤드롭) */}
        <ImageUploader />
        {/* 자연어 프롬프트 */}
        <PromptInput />
        {/* 처리 중/에러 배너 */}
        <ProcessingStatus />

        <div className="flex flex-wrap gap-3">
          {/* 파일 없거나 처리 중이면 비활성 */}
          <Button onClick={() => process()} disabled={isProcessing || !file}>
            처리 시작
          </Button>
          <Button variant="ghost" onClick={() => reset()} disabled={isProcessing}>
            초기화
          </Button>
        </div>

        {/* 결과 영역: job 성공 후에만 내용 표시 */}
        <BeforeAfterViewer />
        <FeedbackButtons />
        {/* Phase 2 배치 업로드 UI 스캐폴드 */}
        <BatchUploader />
      </main>

      <footer className="mt-auto border-t border-slate-800 pt-4 text-xs text-slate-500">
        docs/plan 로직 구조 기반 · YOLO-seg + LangGraph + OpenCV
      </footer>
    </div>
  );
}

/**
 * 자연어 프롬프트 입력.
 * 값은 useAppStore.prompt 에 양방향 바인딩.
 */
import { useAppStore } from "../../store/useAppStore";

export function PromptInput() {
  const prompt = useAppStore((s) => s.prompt);
  const setPrompt = useAppStore((s) => s.setPrompt);

  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium text-slate-200">프롬프트</span>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        placeholder='예: "강아지"만 남기고 배경 블러 처리해줘'
        className="w-full resize-y rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none ring-brand-500 placeholder:text-slate-500 focus:ring-2"
      />
      <p className="text-xs text-slate-500">
        대상 · 블러/크롭 등 자연어로 지정 (Phase 1: 휴리스틱 파서 + YOLO)
      </p>
    </label>
  );
}

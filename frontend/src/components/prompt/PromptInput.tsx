/**
 * 자연어 프롬프트 입력 + 예시 칩.
 * 값은 useAppStore.prompt 에 양방향 바인딩. Ctrl/⌘+Enter 로 처리 시작.
 */
import { useAppStore } from "../../store/useAppStore";
import { ExamplePrompts } from "./ExamplePrompts";

interface Props {
  onSubmit?: () => void;
}

export function PromptInput({ onSubmit }: Props) {
  const prompt = useAppStore((s) => s.prompt);
  const setPrompt = useAppStore((s) => s.setPrompt);

  return (
    <div className="space-y-2">
      <label className="block space-y-2">
        <span className="text-sm font-medium text-slate-200">무엇을 남기거나 지울까요?</span>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) onSubmit?.();
          }}
          rows={3}
          maxLength={1000}
          placeholder="예: 맨 앞에 빨간 안전모 쓴 사람만 남기고 배경 제거"
          className="w-full resize-y rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none ring-brand-500 placeholder:text-slate-500 focus:ring-2"
        />
      </label>
      <p className="text-xs text-slate-500">
        대상 · 위치(맨 앞, 왼쪽에서 두 번째) · 색(빨간 안전모) · 남기기/지우기를 자연어로. Ctrl+Enter 로 시작
      </p>
      <ExamplePrompts onPick={setPrompt} limit={6} />
    </div>
  );
}

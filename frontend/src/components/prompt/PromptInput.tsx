/**
 * 자연어 프롬프트 입력 + 예시 칩.
 * 값은 useAppStore.prompt 에 양방향 바인딩. Ctrl/⌘+Enter 로 처리 시작.
 */
import { useAppStore } from "../../store/useAppStore";
import { ExamplePrompts } from "./ExamplePrompts";

interface Props {
  onSubmit?: () => void;
}

const MAX = 1000;

export function PromptInput({ onSubmit }: Props) {
  const prompt = useAppStore((s) => s.prompt);
  const setPrompt = useAppStore((s) => s.setPrompt);

  return (
    <div className="space-y-3">
      <label className="block space-y-2">
        <span className="sr-only">무엇을 남기거나 지울까요?</span>
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) onSubmit?.();
            }}
            rows={3}
            maxLength={MAX}
            placeholder="예: 맨 앞에 빨간 안전모 쓴 사람만 남기고 배경 제거"
            className="field min-h-[96px] resize-y pb-7 text-[15px] leading-relaxed"
          />
          <span className="pointer-events-none absolute bottom-2 right-3 flex items-center gap-1 text-[11px] text-slate-500">
            <kbd className="rounded border border-slate-700 bg-slate-900 px-1 font-sans">Ctrl</kbd>+
            <kbd className="rounded border border-slate-700 bg-slate-900 px-1 font-sans">Enter</kbd>
            <span className="hidden sm:inline">로 시작</span>
          </span>
        </div>
      </label>
      <p className="text-xs leading-relaxed text-slate-500">
        대상 · 위치(맨 앞, 왼쪽에서 두 번째) · 색(빨간 안전모) · 남기기/지우기를 평소 말투로 적어 주세요.
      </p>
      <ExamplePrompts onPick={setPrompt} limit={6} />
    </div>
  );
}

/**
 * 예시 프롬프트 칩. 누르면 onPick 으로 문장을 넘긴다.
 */
import { EXAMPLES } from "../../data/examples";

interface Props {
  onPick: (text: string) => void;
  limit?: number;
}

export function ExamplePrompts({ onPick, limit }: Props) {
  const items = limit ? EXAMPLES.slice(0, limit) : EXAMPLES;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((ex) => (
        <button
          key={ex.text}
          type="button"
          title={ex.point}
          onClick={() => onPick(ex.text)}
          className="max-w-full rounded-full border border-slate-700/80 bg-slate-900/80 px-3 py-1.5 text-left text-xs text-slate-300 transition hover:-translate-y-px hover:border-brand-500/60 hover:bg-brand-500/10 hover:text-white"
        >
          {ex.text}
        </button>
      ))}
    </div>
  );
}

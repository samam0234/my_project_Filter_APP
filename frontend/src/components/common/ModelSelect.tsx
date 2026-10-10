/**
 * 문장 해석 모델 선택 — "처리하기" 버튼 옆에 둔다 (사진 · GIF · 영상 작업실 공통).
 *
 * - 서버가 알려 준 모델을 보여 주고, 서버에 설치되지 않은 모델은 "미적용"으로 표시하며 고를 수 없다.
 *   서버에서 모델을 내려받으면 "미적용"이 저절로 사라진다 (창으로 돌아올 때 · 30초마다 다시 조회).
 * - 해석을 Ollama 가 맡지 않는 서버(예: LoRA)나 목록을 못 받았을 때는 아무것도 그리지 않는다.
 * - 처리 중에는 바꿀 수 없다 (disabled).
 */
import { useEffect } from "react";
import { Cpu } from "lucide-react";
import { useLlmModelStore } from "../../store/useLlmModelStore";

const POLL_MS = 30_000;

export function ModelSelect({ disabled = false, className = "" }: { disabled?: boolean; className?: string }) {
  const enabled = useLlmModelStore((s) => s.enabled);
  const models = useLlmModelStore((s) => s.models);
  const defaultId = useLlmModelStore((s) => s.defaultId);
  const selected = useLlmModelStore((s) => s.selected);
  const refresh = useLlmModelStore((s) => s.refresh);
  const select = useLlmModelStore((s) => s.select);

  useEffect(() => {
    void refresh();
    const onFocus = () => void refresh();
    window.addEventListener("focus", onFocus);
    const timer = window.setInterval(() => void refresh(), POLL_MS);
    return () => {
      window.removeEventListener("focus", onFocus);
      window.clearInterval(timer);
    };
  }, [refresh]);

  if (!enabled) return null;
  const value = selected ?? defaultId ?? "";
  const note = models.find((m) => m.id === value)?.note;

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label className="inline-flex items-center gap-2 text-xs text-slate-400">
        <Cpu className="h-3.5 w-3.5 shrink-0" aria-hidden />
        <span className="sr-only sm:not-sr-only">해석 모델</span>
        <select
          aria-label="문장 해석 모델"
          value={value}
          disabled={disabled}
          onChange={(e) => select(e.target.value === defaultId ? null : e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-2 text-sm text-slate-100 focus:border-brand-500 focus:outline-none disabled:opacity-60"
        >
          {models.map((m) => (
            <option key={m.id} value={m.id} disabled={!m.available}>
              {m.label}
              {m.available ? "" : " · 미적용"}
            </option>
          ))}
        </select>
      </label>
      {note && <p className="max-w-xs text-xs leading-relaxed text-slate-500">{note}</p>}
    </div>
  );
}

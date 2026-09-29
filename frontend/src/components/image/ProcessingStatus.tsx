/**
 * 처리 중 진행 안내 / 에러 배너.
 *
 * 처리는 서버에서 동기로 15~30초(첫 요청은 모델 로드로 더 김) 걸리므로
 * 경과 시간과 대략의 단계(해석 → 대상 찾기 → 효과)를 보여준다.
 * 단계는 경과 시간 기준 추정치다 (서버가 진행률을 보내지 않음).
 */
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

// 【수동·튜닝】 단계 안내 시각(초) — 실제 처리 시간에 맞게 조정
const STAGES = [
  { after: 0, label: "문장 해석 중 (LLM)" },
  { after: 6, label: "대상 찾는 중 (YOLO 세그멘테이션)" },
  { after: 12, label: "대상 고르고 효과 적용 중" },
  { after: 35, label: "조금 오래 걸리고 있어요 — 첫 요청은 모델을 불러옵니다" },
];

export function ProcessingStatus() {
  const isProcessing = useAppStore((s) => s.isProcessing);
  const error = useAppStore((s) => s.error);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isProcessing) return;
    setElapsed(0);
    const started = Date.now();
    const t = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 500);
    return () => window.clearInterval(t);
  }, [isProcessing]);

  if (!isProcessing && !error) return null;
  const stage = [...STAGES].reverse().find((s) => elapsed >= s.after) ?? STAGES[0];

  return (
    <div className="space-y-2" aria-live="polite">
      {isProcessing && (
        <div className="flex items-center gap-3 rounded-xl border border-brand-700/40 bg-brand-900/20 px-3 py-2 text-sm text-brand-100">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
          <span className="flex-1">{stage.label}</span>
          <span className="tabular-nums text-xs text-brand-100/70">{elapsed}s</span>
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}
    </div>
  );
}

/**
 * 서버가 문장을 어떻게 해석했는지 칩으로 보여준다 (ParsedPrompt).
 *
 * 예: [사람] [배경 제거] [맨 앞 · 1개] [red helmet] [neon yellow vest]
 * 해석이 틀렸으면 사용자가 바로 알아보고 "정답 알려주기" 로 교정할 수 있게 하는 것이 목적.
 */
import type { ReactNode } from "react";
import type { ParsedPrompt } from "../../types";
import { classLabel, effectLabel, positionLabel } from "../../utils/formatters";

function Chip({ children, tone }: { children: ReactNode; tone: string }) {
  return <span className={`rounded-lg px-2 py-1 text-xs ring-1 ring-inset ${tone}`}>{children}</span>;
}

export function selectorSummary(parsed: ParsedPrompt): string | null {
  const s = parsed.selector;
  if (!s) return null;
  const parts: string[] = [];
  if (s.position) {
    parts.push(s.rank && s.rank > 1 ? `${positionLabel(s.position)}에서 ${s.rank}번째` : positionLabel(s.position));
  }
  if (s.count) parts.push(`${s.count}개`);
  else if (s.position) parts.push("1개");
  return parts.length ? parts.join(" · ") : null;
}

export function ParsedPromptView({ parsed }: { parsed?: ParsedPrompt | null }) {
  if (!parsed) return <p className="text-xs text-slate-500">해석 결과 없음</p>;
  const isRemove = parsed.effect === "remove_object";
  const where = selectorSummary(parsed);

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {parsed.target.map((t) => (
        <Chip key={t} tone="bg-brand-500/10 text-brand-100 ring-brand-500/30">
          {classLabel(t)}
        </Chip>
      ))}
      {where && <Chip tone="bg-violet-500/10 text-violet-200 ring-violet-500/30">{where}</Chip>}
      {parsed.selector?.attributes?.map((a) => (
        <Chip key={a} tone="bg-fuchsia-500/10 text-fuchsia-200 ring-fuchsia-500/30">
          {a}
        </Chip>
      ))}
      <span className="px-1 text-xs text-slate-500">→</span>
      <Chip
        tone={
          isRemove
            ? "bg-rose-500/10 text-rose-200 ring-rose-500/30"
            : "bg-emerald-500/10 text-emerald-200 ring-emerald-500/30"
        }
      >
        {isRemove ? "대상 지우기" : `대상 남기고 ${effectLabel(parsed.effect)}`}
        {parsed.effect === "blur" && ` ${parsed.intensity}`}
      </Chip>
      {parsed.crop && parsed.effect !== "crop" && (
        <Chip tone="bg-slate-500/10 text-slate-300 ring-slate-500/30">+ 크롭</Chip>
      )}
    </div>
  );
}

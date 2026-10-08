/**
 * 작업실 입력 칸의 단계 머리 (1 사진 · 2 문장 · 3 처리). done 이면 숫자 배지를 채운다.
 */
import type { ReactNode } from "react";

export function Step({ n, title, done, children }: { n: number; title: string; done?: boolean; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2.5 text-sm font-semibold text-slate-100">
        <span className={done ? "step-dot bg-brand-500 text-white ring-brand-400" : "step-dot"}>{n}</span>
        {title}
      </h2>
      {children}
    </section>
  );
}

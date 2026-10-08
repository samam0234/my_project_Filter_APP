/**
 * 공통 버튼. variant: primary | secondary | ghost | danger · size: sm | md | lg
 * type 기본 button (폼 submit 방지).
 */
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: Variant;
  size?: Size;
}

const styles: Record<Variant, string> = {
  primary:
    "bg-gradient-to-b from-brand-500 to-brand-600 text-white shadow-glow hover:from-brand-400 hover:to-brand-500 disabled:shadow-none",
  secondary: "border border-slate-700 bg-slate-900 text-slate-100 hover:border-slate-600 hover:bg-slate-800",
  ghost: "bg-transparent text-slate-300 hover:bg-slate-800/70 hover:text-white",
  danger: "bg-rose-600 text-white hover:bg-rose-500",
};

const sizes: Record<Size, string> = {
  sm: "rounded-lg px-3 py-1.5 text-xs",
  md: "rounded-xl px-4 py-2 text-sm",
  lg: "rounded-xl px-5 py-2.5 text-sm",
};

/** 링크(<a>, <Link>)를 버튼처럼 보이게 할 때 같은 모양을 쓴다 */
export function buttonClass(variant: Variant = "primary", size: Size = "md", extra = ""): string {
  return `inline-flex items-center justify-center gap-2 font-medium transition active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${sizes[size]} ${extra}`;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  ...rest
}: Props) {
  return (
    <button type="button" disabled={disabled} className={buttonClass(variant, size, className)} {...rest}>
      {children}
    </button>
  );
}

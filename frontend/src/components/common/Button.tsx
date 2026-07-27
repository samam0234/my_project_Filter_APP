import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: Variant;
}

const styles: Record<Variant, string> = {
  primary:
    "bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-900/30",
  secondary: "bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-600",
  ghost: "bg-transparent hover:bg-slate-800 text-slate-200",
  danger: "bg-rose-700 hover:bg-rose-600 text-white",
};

export function Button({
  children,
  variant = "primary",
  className = "",
  disabled,
  ...rest
}: Props) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

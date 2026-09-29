/**
 * 계정 화면 공통 부품 — 가운데 카드 · 입력 필드 · 비밀번호 보기 토글 · 안내/오류 박스.
 */
import { useId, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { Eye, EyeOff } from "lucide-react";

export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-md py-6">
      <div className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl shadow-black/20 sm:p-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-white">{title}</h1>
          {description && <p className="text-sm text-slate-400">{description}</p>}
        </div>
        {children}
      </div>
      {footer && <div className="mt-4 text-center text-sm text-slate-400">{footer}</div>}
    </div>
  );
}

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string | null;
}

const inputClass =
  "w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/40 aria-[invalid=true]:border-rose-600";

export function Field({ label, hint, error, id, ...rest }: FieldProps) {
  const auto = useId();
  const inputId = id ?? auto;
  return (
    <label htmlFor={inputId} className="block space-y-1.5">
      <span className="text-sm text-slate-200">{label}</span>
      <input id={inputId} aria-invalid={Boolean(error)} className={inputClass} {...rest} />
      {error ? (
        <span className="block text-xs text-rose-300">{error}</span>
      ) : (
        hint && <span className="block text-xs text-slate-500">{hint}</span>
      )}
    </label>
  );
}

export function PasswordField(props: Omit<FieldProps, "type">) {
  const [show, setShow] = useState(false);
  const auto = useId();
  const inputId = props.id ?? auto;
  const { label, hint, error, ...rest } = props;
  return (
    <label htmlFor={inputId} className="block space-y-1.5">
      <span className="text-sm text-slate-200">{label}</span>
      <span className="relative block">
        <input
          id={inputId}
          type={show ? "text" : "password"}
          aria-invalid={Boolean(error)}
          className={`${inputClass} pr-10`}
          {...rest}
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          aria-label={show ? "비밀번호 숨기기" : "비밀번호 보기"}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-500 hover:text-slate-200"
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </span>
      {error ? (
        <span className="block text-xs text-rose-300">{error}</span>
      ) : (
        hint && <span className="block text-xs text-slate-500">{hint}</span>
      )}
    </label>
  );
}

export function Notice({ tone, children }: { tone: "error" | "info" | "success"; children: ReactNode }) {
  const tones = {
    error: "border-rose-800/50 bg-rose-950/40 text-rose-200",
    info: "border-brand-700/40 bg-brand-900/20 text-brand-100",
    success: "border-emerald-800/50 bg-emerald-950/30 text-emerald-200",
  };
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`rounded-xl border px-3 py-2 text-sm ${tones[tone]}`}>
      {children}
    </div>
  );
}

// 백엔드 규칙과 같게 (backend/app/core/passwords.py)
export const USERNAME_RE = /^[a-z0-9_]{4,20}$/;
export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function passwordProblem(pw: string): string | null {
  if (pw.length < 8 || pw.length > 64) return "8~64자로 입력해 주세요.";
  if (!/[A-Za-z]/.test(pw) || !/\d/.test(pw)) return "영문과 숫자를 모두 넣어 주세요.";
  return null;
}

/** 로그인 후 돌아갈 곳 — 앱 내부 경로만 허용 (오픈 리다이렉트 방지) */
export function safeNext(search: string, fallback = "/"): string {
  const next = new URLSearchParams(search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : fallback;
}

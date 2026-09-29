/**
 * 비밀번호 찾기 (/find-password) — 2단계.
 *   1) 아이디 + 이메일 → 6자리 인증 코드 메일 (항상 같은 안내)
 *   2) 코드 + 새 비밀번호 → 재설정. 성공하면 모든 기기 로그아웃 → 로그인 화면으로
 */
import { useState, type FormEvent } from "react";
import { KeyRound, Mail } from "lucide-react";
import { errorMessage, passwordCodeRequest, passwordResetRequest } from "../../api/client";
import {
  AuthCard,
  EMAIL_RE,
  Field,
  Notice,
  PasswordField,
  USERNAME_RE,
  passwordProblem,
} from "../../components/auth/AuthForm";
import { Button } from "../../components/common/Button";
import { Link, navigate } from "../../router";
import { useAuthStore } from "../../store/useAuthStore";

export function FindPasswordPage() {
  const [step, setStep] = useState<"request" | "reset">("request");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const requestCode = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!USERNAME_RE.test(username.trim().toLowerCase()) || !EMAIL_RE.test(email.trim())) {
      setError("아이디와 이메일을 정확히 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await passwordCodeRequest(username.trim().toLowerCase(), email.trim());
      setInfo(res.message);
      setStep("reset");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const reset = async (e: FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(code.trim())) {
      setError("메일로 받은 6자리 숫자를 입력해 주세요.");
      return;
    }
    const problem = passwordProblem(password);
    if (problem) {
      setError(`새 비밀번호: ${problem}`);
      return;
    }
    if (password !== confirm) {
      setError("새 비밀번호가 서로 다릅니다.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await passwordResetRequest(username.trim().toLowerCase(), code.trim(), password);
      // 서버가 모든 세션을 끊었으므로 화면 상태도 비로그인으로
      useAuthStore.setState({ user: null, status: "guest" });
      navigate("/login?reset=1", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="비밀번호 찾기"
      description={
        step === "request"
          ? "아이디와 가입 이메일을 입력하면 인증 코드를 보내 드려요."
          : "메일로 받은 인증 코드와 새 비밀번호를 입력해 주세요."
      }
      footer={
        <span className="inline-flex gap-3">
          <Link to="/login" className="text-brand-500 hover:text-brand-100">
            로그인
          </Link>
          <span className="text-slate-700">|</span>
          <Link to="/find-id" className="hover:text-white">
            아이디 찾기
          </Link>
        </span>
      }
    >
      <ol className="flex gap-2 text-xs">
        {["코드 받기", "새 비밀번호"].map((label, i) => {
          const active = (i === 0 && step === "request") || (i === 1 && step === "reset");
          return (
            <li
              key={label}
              className={`flex-1 rounded-lg px-2 py-1.5 text-center ${
                active ? "bg-slate-800 text-white" : "text-slate-500"
              }`}
            >
              {i + 1}. {label}
            </li>
          );
        })}
      </ol>

      {step === "request" ? (
        <form className="space-y-4" onSubmit={(e) => void requestCode(e)} noValidate>
          <Field
            label="아이디"
            autoComplete="username"
            autoCapitalize="none"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase())}
          />
          <Field
            label="가입 이메일"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {error && <Notice tone="error">{error}</Notice>}
          <Button type="submit" className="w-full py-2.5" disabled={loading}>
            <Mail className="h-4 w-4" /> {loading ? "보내는 중…" : "인증 코드 받기"}
          </Button>
        </form>
      ) : (
        <form className="space-y-4" onSubmit={(e) => void reset(e)} noValidate>
          {info && <Notice tone="info">{info}</Notice>}
          <Field
            label="인증 코드 (6자리)"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            hint="코드는 10분 동안 유효하고, 5번 틀리면 다시 받아야 해요."
          />
          <PasswordField
            label="새 비밀번호"
            autoComplete="new-password"
            hint="8~64자, 영문과 숫자를 모두 포함"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <PasswordField
            label="새 비밀번호 확인"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
          {error && <Notice tone="error">{error}</Notice>}
          <Button type="submit" className="w-full py-2.5" disabled={loading}>
            <KeyRound className="h-4 w-4" /> {loading ? "바꾸는 중…" : "비밀번호 바꾸기"}
          </Button>
          <div className="flex justify-between text-xs text-slate-400">
            <button type="button" className="hover:text-white" onClick={() => void requestCode()} disabled={loading}>
              코드 다시 받기
            </button>
            <button
              type="button"
              className="hover:text-white"
              onClick={() => {
                setStep("request");
                setError(null);
              }}
            >
              아이디·이메일 다시 입력
            </button>
          </div>
        </form>
      )}
    </AuthCard>
  );
}

/**
 * 로그인 (/login?next=/history) — 성공하면 next(앱 내부 경로) 또는 홈으로.
 */
import { useState, type FormEvent } from "react";
import { LogIn } from "lucide-react";
import { errorMessage } from "../../api/client";
import { AuthCard, Field, Notice, PasswordField, safeNext } from "../../components/auth/AuthForm";
import { Button } from "../../components/common/Button";
import { Link, navigate, useSearch } from "../../router";
import { useAuthStore } from "../../store/useAuthStore";

export function LoginPage() {
  const search = useSearch();
  const login = useAuthStore((s) => s.login);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const reset = new URLSearchParams(search).get("reset") === "1";

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("아이디와 비밀번호를 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await login(username.trim(), password);
      navigate(safeNext(search), { replace: true });
    } catch (err) {
      setError(errorMessage(err, "로그인에 실패했습니다."));
      setPassword("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="로그인"
      description="로그인하면 내 작업을 모아 볼 수 있어요."
      footer={
        <>
          아직 계정이 없나요?{" "}
          <Link to="/signup" className="text-brand-500 hover:text-brand-100">
            회원가입
          </Link>
        </>
      }
    >
      {reset && <Notice tone="success">비밀번호를 바꿨습니다. 새 비밀번호로 로그인해 주세요.</Notice>}
      <form className="space-y-4" onSubmit={(e) => void submit(e)} noValidate>
        <Field
          label="아이디"
          autoComplete="username"
          autoCapitalize="none"
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <PasswordField
          label="비밀번호"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <Notice tone="error">{error}</Notice>}
        <Button type="submit" className="w-full py-2.5" disabled={loading}>
          <LogIn className="h-4 w-4" /> {loading ? "로그인 중…" : "로그인"}
        </Button>
      </form>
      <div className="flex justify-center gap-3 text-xs text-slate-400">
        <Link to="/find-id" className="hover:text-white">
          아이디 찾기
        </Link>
        <span className="text-slate-700">|</span>
        <Link to="/find-password" className="hover:text-white">
          비밀번호 찾기
        </Link>
      </div>
    </AuthCard>
  );
}

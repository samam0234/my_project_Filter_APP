/**
 * 회원가입 (/signup) — 입력 즉시 규칙 안내, 가입하면 바로 로그인 상태.
 * 규칙은 백엔드(core/passwords.py)와 같다. 최종 판정은 서버.
 */
import { useState, type ChangeEvent, type FormEvent } from "react";
import { UserPlus } from "lucide-react";
import { errorMessage } from "../../api/client";
import {
  AuthCard,
  EMAIL_RE,
  Field,
  Notice,
  PasswordField,
  USERNAME_RE,
  passwordProblem,
  safeNext,
} from "../../components/auth/AuthForm";
import { Button } from "../../components/common/Button";
import { Link, navigate, useSearch } from "../../router";
import { useAuthStore } from "../../store/useAuthStore";

export function SignupPage() {
  const search = useSearch();
  const signup = useAuthStore((s) => s.signup);
  const [form, setForm] = useState({ username: "", email: "", name: "", password: "", confirm: "" });
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const set = (key: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: key === "username" ? e.target.value.toLowerCase() : e.target.value }));
  const blur = (key: string) => () => setTouched((t) => ({ ...t, [key]: true }));

  const problems = {
    username: USERNAME_RE.test(form.username) ? null : "영문 소문자·숫자·밑줄(_) 4~20자",
    email: EMAIL_RE.test(form.email.trim()) ? null : "올바른 이메일 주소를 입력해 주세요.",
    password: passwordProblem(form.password),
    confirm: form.confirm === form.password ? null : "비밀번호가 서로 다릅니다.",
  };
  const show = (key: keyof typeof problems) => (touched[key] ? problems[key] : null);
  const valid = Object.values(problems).every((p) => p === null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched({ username: true, email: true, password: true, confirm: true });
    if (!valid) return;
    setLoading(true);
    setError(null);
    try {
      await signup({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        display_name: form.name.trim() || undefined,
      });
      navigate(safeNext(search), { replace: true });
    } catch (err) {
      setError(errorMessage(err, "가입에 실패했습니다."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="회원가입"
      description="이메일은 아이디·비밀번호를 찾을 때 쓰여요."
      footer={
        <>
          이미 계정이 있나요?{" "}
          <Link to="/login" className="text-brand-400 hover:text-brand-200">
            로그인
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={(e) => void submit(e)} noValidate>
        <Field
          label="아이디"
          autoComplete="username"
          autoCapitalize="none"
          autoFocus
          hint="영문 소문자·숫자·밑줄(_) 4~20자"
          value={form.username}
          onChange={set("username")}
          onBlur={blur("username")}
          error={show("username")}
        />
        <Field
          label="이메일"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={set("email")}
          onBlur={blur("email")}
          error={show("email")}
        />
        <Field
          label="이름 (선택)"
          autoComplete="nickname"
          maxLength={50}
          hint="화면에 표시될 이름"
          value={form.name}
          onChange={set("name")}
        />
        <PasswordField
          label="비밀번호"
          autoComplete="new-password"
          hint="8~64자, 영문과 숫자를 모두 포함"
          value={form.password}
          onChange={set("password")}
          onBlur={blur("password")}
          error={show("password")}
        />
        <PasswordField
          label="비밀번호 확인"
          autoComplete="new-password"
          value={form.confirm}
          onChange={set("confirm")}
          onBlur={blur("confirm")}
          error={show("confirm")}
        />
        <div className="space-y-1.5 rounded-xl bg-slate-950/50 p-3 text-xs leading-relaxed text-slate-400 ring-1 ring-inset ring-slate-800">
          <p className="font-medium text-slate-300">가입하면 이렇게 처리돼요</p>
          <ul className="list-disc space-y-1 pl-4">
            <li>올린 사진 · 영상 · GIF 와 결과 파일은 서버에 24시간 보관한 뒤 자동으로 지워요.</li>
            <li>요청 문장과 해석 결과는 운영자가 검수한 뒤 문장 이해 품질을 높이는 학습에 쓰일 수 있어요.</li>
            <li>계정을 지우면 작업 기록과 파일도 함께 지우고, 학습 후보 문장은 계정과의 연결을 끊어요.</li>
          </ul>
        </div>
        {error && <Notice tone="error">{error}</Notice>}
        <Button type="submit" className="w-full py-2.5" disabled={loading}>
          <UserPlus className="h-4 w-4" /> {loading ? "가입 중…" : "가입하기"}
        </Button>
      </form>
    </AuthCard>
  );
}

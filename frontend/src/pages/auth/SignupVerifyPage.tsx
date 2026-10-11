/**
 * 회원가입 (/signup/verify) 2단계 — 메일로 받은 일련번호를 입력해 가입을 끝낸다.
 *
 * 메일의 [회원가입 인증] 버튼이 이 화면(/signup/verify?email=…)을 연다. 일련번호는 대소문자 · 하이픈과 상관없이
 * 붙여넣거나 직접 입력하면 된다 (입력 칸이 4글자마다 하이픈을 넣어 준다).
 * 인증에 성공하면 계정이 만들어지고 바로 로그인 상태가 된다. 일련번호는 30분 동안만 유효하고 5번 틀리면 새로 받아야 한다.
 */
import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { MailCheck, RefreshCw } from "lucide-react";
import { errorMessage, signupResendRequest, signupVerifyRequest } from "../../api/client";
import { AuthCard, EMAIL_RE, Field, Notice, safeNext } from "../../components/auth/AuthForm";
import { Button } from "../../components/common/Button";
import { Link, navigate, useSearch } from "../../router";
import { useAuthStore } from "../../store/useAuthStore";

/** 입력을 비교용 8글자로 줄이고 4-4 로 다시 하이픈을 넣는다 (최대 9칸). */
export function formatSerial(value: string): string {
  const raw = value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
  return raw.length > 4 ? `${raw.slice(0, 4)}-${raw.slice(4)}` : raw;
}

// 【수동】 백엔드 AUTH_CODE_RESEND_SECONDS(60) 와 맞춤 — 서버가 최종 판단하므로 어긋나도 안내만 달라진다
const RESEND_SECONDS = 60;

export function SignupVerifyPage() {
  const search = useSearch();
  const setUser = useAuthStore((s) => s.setUser);
  const params = new URLSearchParams(search);
  const emailFromLink = params.get("email") ?? "";

  const [email, setEmail] = useState(emailFromLink);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  // 신청 직후 이 화면으로 왔다면(링크에 email 만 있고 아직 메일을 못 열었을 수 있다) 바로 다시 받기를 막지 않는다
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = window.setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => window.clearTimeout(t);
  }, [cooldown]);

  const emailOk = EMAIL_RE.test(email.trim());
  const codeOk = code.replace("-", "").length === 8;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!emailOk || !codeOk) return;
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      setUser(await signupVerifyRequest(email.trim(), code));
      navigate(safeNext(search), { replace: true });
    } catch (err) {
      setError(errorMessage(err, "인증하지 못했어요."));
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (!emailOk) return;
    setResending(true);
    setError(null);
    try {
      const res = await signupResendRequest(email.trim());
      setInfo(res.message);
      setCode("");
      setCooldown(RESEND_SECONDS);
    } catch (err) {
      setError(errorMessage(err, "다시 보내지 못했어요."));
    } finally {
      setResending(false);
    }
  };

  return (
    <AuthCard
      title="이메일 인증"
      description={
        emailFromLink ? (
          <>
            <b className="text-slate-200">{emailFromLink}</b> 로 보낸 메일의 <b className="text-slate-200">일련번호</b>를 입력해
            주세요. (2/2 단계)
          </>
        ) : (
          "가입 신청 때 입력한 이메일과, 그 메일로 받은 일련번호를 입력해 주세요. (2/2 단계)"
        )
      }
      footer={
        <>
          정보를 잘못 입력했나요?{" "}
          <Link to="/signup" className="text-brand-400 hover:text-brand-200">
            처음부터 다시 가입
          </Link>
        </>
      }
    >
      <form className="space-y-4" onSubmit={(e) => void submit(e)} noValidate>
        {!emailFromLink && (
          <Field
            label="이메일"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
          />
        )}
        <Field
          label="일련번호"
          autoComplete="one-time-code"
          autoCapitalize="characters"
          autoFocus
          spellCheck={false}
          maxLength={9}
          placeholder="XXXX-XXXX"
          hint="메일에 적힌 8글자예요. 붙여넣어도 돼요."
          className="field text-center font-mono text-xl uppercase tracking-[0.25em]"
          value={code}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setCode(formatSerial(e.target.value))}
        />
        {info && <Notice tone="info">{info}</Notice>}
        {error && <Notice tone="error">{error}</Notice>}
        <Button type="submit" className="w-full py-2.5" disabled={loading || !emailOk || !codeOk}>
          <MailCheck className="h-4 w-4" /> {loading ? "확인 중…" : "인증하고 가입 완료"}
        </Button>
        <div className="space-y-1 text-center text-xs text-slate-500">
          <p>메일이 오지 않으면 스팸함을 확인해 주세요. 보통 1분 안에 도착해요.</p>
          <button
            type="button"
            onClick={() => void resend()}
            disabled={resending || cooldown > 0 || !emailOk}
            className="inline-flex items-center gap-1 text-brand-400 hover:text-brand-200 disabled:cursor-not-allowed disabled:text-slate-600"
          >
            <RefreshCw className={`h-3 w-3 ${resending ? "animate-spin" : ""}`} />
            {cooldown > 0 ? `일련번호 다시 받기 (${cooldown}초)` : "일련번호 다시 받기"}
          </button>
        </div>
      </form>
    </AuthCard>
  );
}

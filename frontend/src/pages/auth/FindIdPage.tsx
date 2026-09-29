/**
 * 아이디 찾기 (/find-id) — 가입 이메일로 아이디를 보낸다.
 * 계정 존재 여부를 알려주지 않도록 서버는 항상 같은 안내를 돌려준다.
 */
import { useState, type FormEvent } from "react";
import { Mail } from "lucide-react";
import { errorMessage, findIdRequest } from "../../api/client";
import { AuthCard, EMAIL_RE, Field, Notice } from "../../components/auth/AuthForm";
import { Button } from "../../components/common/Button";
import { Link } from "../../router";

export function FindIdPage() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!EMAIL_RE.test(email.trim())) {
      setError("올바른 이메일 주소를 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setDone((await findIdRequest(email.trim())).message);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="아이디 찾기"
      description="가입할 때 쓴 이메일로 아이디를 보내 드려요."
      footer={
        <span className="inline-flex gap-3">
          <Link to="/login" className="text-brand-500 hover:text-brand-100">
            로그인
          </Link>
          <span className="text-slate-700">|</span>
          <Link to="/find-password" className="hover:text-white">
            비밀번호 찾기
          </Link>
        </span>
      }
    >
      {done ? (
        <div className="space-y-4">
          <Notice tone="success">{done}</Notice>
          <p className="text-xs text-slate-400">
            메일이 오지 않으면 스팸함을 확인하거나, 잠시 뒤 다시 시도해 주세요.
          </p>
          <Button variant="secondary" className="w-full" onClick={() => setDone(null)}>
            다른 이메일로 찾기
          </Button>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={(e) => void submit(e)} noValidate>
          <Field
            label="이메일"
            type="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {error && <Notice tone="error">{error}</Notice>}
          <Button type="submit" className="w-full py-2.5" disabled={loading}>
            <Mail className="h-4 w-4" /> {loading ? "보내는 중…" : "아이디 받기"}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}

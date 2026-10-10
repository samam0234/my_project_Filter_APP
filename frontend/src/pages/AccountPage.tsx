/**
 * 내 계정 (/account) — 로그인 회원 전용. 헤더의 프로필을 눌러 들어온다.
 *
 * 구역은 URL 쿼리 ?tab= 으로 고른다 (새로고침 · 링크 공유 가능):
 *   profile  내 정보   — 아이디 · 이메일 · 가입일, 표시 이름 수정, 이용 현황(작업 개수), 바로가기
 *   history  작업 기록 — 사진 · 영상 · GIF 목록 (예전 /history 가 여기로 옮겨졌다)
 *   security 보안      — 비밀번호 변경 (다른 기기 로그아웃), 모든 기기에서 로그아웃
 *   data     보관 · 탈퇴 — 보관 기간 안내, 처리방침 링크, 계정 탈퇴 (비밀번호 + 아이디 확인)
 */
import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Database, History, Layers, LogOut, ShieldCheck, Trash2, UserRound } from "lucide-react";
import {
  changePasswordRequest,
  deleteAccountRequest,
  errorMessage,
  logoutAllRequest,
  updateProfileRequest,
} from "../api/client";
import { Field, Notice, PasswordField, passwordProblem } from "../components/auth/AuthForm";
import { RequireLogin } from "../components/auth/RequireLogin";
import { HistoryPanel } from "../components/account/HistoryPanel";
import { Button } from "../components/common/Button";
import { PageHeader } from "../components/common/PageHeader";
import { useJobs } from "../hooks/useApi";
import { Link, navigate, useSearch } from "../router";
import { useAppStore } from "../store/useAppStore";
import { displayName, useAuthStore } from "../store/useAuthStore";
import { formatDateTime } from "../utils/formatters";

const TABS = [
  { id: "profile", label: "내 정보", icon: UserRound },
  { id: "history", label: "작업 기록", icon: History },
  { id: "security", label: "보안", icon: ShieldCheck },
  { id: "data", label: "보관 · 탈퇴", icon: Database },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function AccountPage() {
  return (
    <RequireLogin title="내 계정은 로그인 회원 전용이에요" reason="로그인하면 내 정보와 작업 기록을 보고 계정을 관리할 수 있어요.">
      <Account />
    </RequireLogin>
  );
}

function Account() {
  const search = useSearch();
  const user = useAuthStore((s) => s.user);
  const raw = new URLSearchParams(search).get("tab");
  const tab: TabId = TABS.some((t) => t.id === raw) ? (raw as TabId) : "profile";

  const goTab = (id: TabId) => navigate(id === "profile" ? "/account" : `/account?tab=${id}`, { replace: true });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="내 계정"
        title={user ? displayName(user) : "내 계정"}
        description="내 정보 · 작업 기록 · 보안 설정을 한곳에서 관리해요."
      />
      <div role="tablist" aria-label="계정 구역" className="flex flex-wrap gap-1 rounded-xl border border-slate-800 bg-slate-900/50 p-1">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => goTab(id)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              tab === id ? "bg-slate-800 text-white shadow-card" : "text-slate-400 hover:text-slate-100"
            }`}
          >
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>
      {tab === "profile" && <ProfileTab />}
      {tab === "history" && <HistoryPanel />}
      {tab === "security" && <SecurityTab />}
      {tab === "data" && <DataTab />}
    </div>
  );
}

function Section({ title, description, children }: { title: string; description?: ReactNode; children: ReactNode }) {
  return (
    <section className="card space-y-4 p-5 sm:p-6">
      <div className="space-y-1">
        <h2 className="text-base font-semibold text-white">{title}</h2>
        {description && <p className="text-sm leading-relaxed text-slate-400">{description}</p>}
      </div>
      {children}
    </section>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex gap-3 text-sm">
      <dt className="w-24 shrink-0 text-slate-500">{label}</dt>
      <dd className="min-w-0 flex-1 break-all text-slate-200">{children}</dd>
    </div>
  );
}

// ---------------------------------------------------------------- 내 정보

function ProfileTab() {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.display_name ?? "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const { data: jobs } = useJobs(200);

  const usage = useMemo(() => {
    const c = { total: 0, image: 0, video: 0, gif: 0, failed: 0 };
    jobs?.forEach((j) => {
      c.total += 1;
      const k = (j.kind ?? "image") as "image" | "video" | "gif";
      c[k] += 1;
      if (j.status === "failed") c.failed += 1;
    });
    return c;
  }, [jobs]);

  if (!user) return null;
  const changed = name.trim() !== (user.display_name ?? "");

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      setUser(await updateProfileRequest(name.trim()));
      setMsg({ tone: "success", text: "표시 이름을 바꿨어요." });
    } catch (err) {
      setMsg({ tone: "error", text: errorMessage(err, "저장하지 못했어요.") });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Section title="내 정보" description="아이디와 이메일은 바꿀 수 없어요. 이메일은 아이디 · 비밀번호 찾기에 쓰여요.">
        <dl className="space-y-2">
          <Row label="아이디">{user.username}</Row>
          <Row label="이메일">{user.email}</Row>
          <Row label="가입일">{formatDateTime(user.created_at)}</Row>
        </dl>
        <form onSubmit={save} className="space-y-3 border-t border-slate-800 pt-4">
          <Field
            label="표시 이름"
            value={name}
            maxLength={50}
            onChange={(e) => setName(e.target.value)}
            hint="헤더와 이 화면에 보이는 이름이에요. 비워 두면 아이디가 보여요."
          />
          {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
          <Button type="submit" disabled={busy || !changed}>
            저장
          </Button>
        </form>
      </Section>

      <div className="space-y-5">
        <Section title="이용 현황" description="최근 200건 안에서 센 내 작업이에요.">
          <dl className="grid grid-cols-2 gap-3 text-center sm:grid-cols-4">
            {[
              ["전체", usage.total],
              ["사진", usage.image],
              ["영상", usage.video],
              ["GIF", usage.gif],
            ].map(([label, n]) => (
              <div key={label} className="rounded-xl border border-slate-800 bg-slate-900/50 px-2 py-3">
                <dd className="text-xl font-bold text-white">{n}</dd>
                <dt className="text-xs text-slate-500">{label}</dt>
              </div>
            ))}
          </dl>
          {usage.failed > 0 && <p className="text-xs text-slate-500">그중 {usage.failed}건은 처리하지 못했어요.</p>}
        </Section>
        <Section title="바로가기">
          <div className="flex flex-wrap gap-2">
            <Link to="/account?tab=history" className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:border-slate-500">
              <History className="h-4 w-4" /> 작업 기록
            </Link>
            <Link to="/batch" className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:border-slate-500">
              <Layers className="h-4 w-4" /> 배치
            </Link>
          </div>
        </Section>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- 보안

function SecurityTab() {
  const [form, setForm] = useState({ current: "", next: "", again: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [allBusy, setAllBusy] = useState(false);

  const problems = {
    next: form.next ? passwordProblem(form.next) : null,
    again: form.again && form.again !== form.next ? "새 비밀번호와 같지 않아요." : null,
  };
  const ready = form.current && form.next && form.again && !problems.next && !problems.again;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!ready) return;
    setBusy(true);
    setMsg(null);
    try {
      const res = await changePasswordRequest(form.current, form.next);
      setForm({ current: "", next: "", again: "" });
      setMsg({ tone: "success", text: res.message });
    } catch (err) {
      setMsg({ tone: "error", text: errorMessage(err, "비밀번호를 바꾸지 못했어요.") });
    } finally {
      setBusy(false);
    }
  };

  const logoutAll = async () => {
    setAllBusy(true);
    try {
      await logoutAllRequest();
    } finally {
      useAuthStore.getState().clear();
      useAppStore.getState().setResult(null);
      setAllBusy(false);
      navigate("/login");
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Section title="비밀번호 변경" description="바꾸면 지금 쓰는 기기만 로그인이 유지되고 다른 기기는 로그아웃돼요.">
        <form onSubmit={submit} className="space-y-3">
          <PasswordField
            label="현재 비밀번호"
            autoComplete="current-password"
            value={form.current}
            onChange={(e) => setForm({ ...form, current: e.target.value })}
          />
          <PasswordField
            label="새 비밀번호"
            autoComplete="new-password"
            value={form.next}
            error={problems.next}
            hint="8~64자, 영문과 숫자를 모두 넣어 주세요."
            onChange={(e) => setForm({ ...form, next: e.target.value })}
          />
          <PasswordField
            label="새 비밀번호 확인"
            autoComplete="new-password"
            value={form.again}
            error={problems.again}
            onChange={(e) => setForm({ ...form, again: e.target.value })}
          />
          {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
          <Button type="submit" disabled={busy || !ready}>
            비밀번호 바꾸기
          </Button>
        </form>
      </Section>
      <Section
        title="모든 기기에서 로그아웃"
        description="공용 PC 에서 로그인한 채로 두었거나 계정이 걱정될 때 쓰세요. 지금 기기도 로그아웃돼요."
      >
        <Button variant="secondary" onClick={logoutAll} disabled={allBusy}>
          <LogOut className="h-4 w-4" /> 모든 기기에서 로그아웃
        </Button>
      </Section>
    </div>
  );
}

// ---------------------------------------------------------------- 보관 · 탈퇴

function DataTab() {
  const user = useAuthStore((s) => s.user);
  const [form, setForm] = useState({ password: "", confirm: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return null;
  const ready = form.password && form.confirm.trim().toLowerCase() === user.username;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!ready) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAccountRequest(form.password, form.confirm.trim());
      useAuthStore.getState().clear();
      useAppStore.getState().setResult(null);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err, "탈퇴하지 못했어요."));
      setBusy(false);
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Section title="내 데이터는 이렇게 보관돼요">
        <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-slate-300">
          <li>사진 · 영상 · GIF 의 원본과 결과는 서버에 기본 24시간 보관되고, 지나면 지워져요. 작업 기록(문장 · 상태)은 남아요.</li>
          <li>처리에 실패하거나 해석이 불확실했던 사진은 서비스 개선을 위해 최대 30일 보관될 수 있어요.</li>
          <li>비밀번호는 암호화해 저장하며 운영자도 볼 수 없어요.</li>
        </ul>
        <p className="text-sm text-slate-400">
          자세한 내용은{" "}
          <Link to="/privacy" className="text-brand-400 hover:text-brand-200">
            개인정보 처리방침
          </Link>{" "}
          ·{" "}
          <Link to="/terms" className="text-brand-400 hover:text-brand-200">
            이용약관
          </Link>
          에서 볼 수 있어요.
        </p>
      </Section>
      <Section
        title="계정 탈퇴"
        description="탈퇴하면 내 작업 · 배치 · 영상이 모두 지워지고 되돌릴 수 없어요. 문장 해석 학습에 이미 쓰인 익명 데이터는 계정과 연결이 끊긴 채 남아요."
      >
        <form onSubmit={submit} className="space-y-3">
          <PasswordField
            label="비밀번호"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <Field
            label={`확인을 위해 아이디(${user.username})를 입력해 주세요`}
            value={form.confirm}
            autoComplete="off"
            onChange={(e) => setForm({ ...form, confirm: e.target.value })}
          />
          {error && <Notice tone="error">{error}</Notice>}
          <Button type="submit" variant="danger" disabled={busy || !ready}>
            <Trash2 className="h-4 w-4" /> 계정 탈퇴
          </Button>
        </form>
      </Section>
    </div>
  );
}

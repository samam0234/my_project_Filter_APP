/**
 * 홈 (/) — 서비스 소개 · 할 수 있는 것 · 동작 방식 · 빠른 시작 · 최근 작업.
 */
import { ArrowRight, Crosshair, Eraser, Focus, ScanSearch, Sparkles, Wand2 } from "lucide-react";
import { Link, navigate } from "../router";
import { useJobs } from "../hooks/useApi";
import { useAppStore } from "../store/useAppStore";
import { useAuthStore } from "../store/useAuthStore";
import { ExamplePrompts } from "../components/prompt/ExamplePrompts";
import { JobCard } from "../components/jobs/JobCard";
import { EmptyBlock } from "../components/common/States";

const FEATURES = [
  {
    icon: Focus,
    title: "원하는 것만 남기기",
    body: "“강아지만 남기고 배경 제거” — 대상만 남기고 배경을 투명하게, 흐리게, 또는 잘라냅니다.",
  },
  {
    icon: Crosshair,
    title: "특정 한 명·하나 고르기",
    body: "“맨 앞 빨간 안전모 쓴 사람”, “왼쪽에서 두 번째” — 위치·순서·개수·색으로 골라요.",
  },
  {
    icon: Eraser,
    title: "필요 없는 것 지우기",
    body: "“오른쪽 사람 지워줘”, “흰색 차 없애줘” — 고른 대상을 지우고 주변으로 메웁니다.",
  },
];

const STEPS = [
  { icon: Sparkles, title: "문장 해석", body: "LLM 이 대상 · 조건 · 하고 싶은 것을 구조화" },
  { icon: ScanSearch, title: "대상 찾기", body: "YOLO26s-seg 가 사물을 픽셀 단위로 분리" },
  { icon: Wand2, title: "고르고 적용", body: "조건에 맞는 것만 골라 남기기 / 지우기" },
];

export function HomePage() {
  const setPrompt = useAppStore((s) => s.setPrompt);
  const loggedIn = useAuthStore((s) => s.status === "user");
  const { data: jobs } = useJobs(4, loggedIn);

  const tryPrompt = (text: string) => {
    setPrompt(text);
    navigate("/studio");
  };

  return (
    <div className="space-y-14">
      <section className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-500">Cut &amp; Keep</p>
          <h1 className="text-3xl font-bold leading-tight text-white sm:text-5xl">
            말로 하면,
            <br />
            원하는 것만 남깁니다
          </h1>
          <p className="max-w-xl text-slate-400">
            사진을 올리고 한 문장으로 요청하세요. 사람·사물을 찾아 배경을 지우거나, 여러 명 중
            특정 한 명만 남기거나, 필요 없는 대상을 지워 드립니다.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/studio"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-brand-900/30 hover:bg-brand-500"
            >
              작업 시작하기 <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/guide"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-5 py-2.5 text-sm text-slate-200 hover:border-slate-500"
            >
              프롬프트 쓰는 법
            </Link>
          </div>
        </div>
        <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
          <p className="text-sm font-medium text-slate-200">이렇게 말해 보세요</p>
          <ExamplePrompts onPick={tryPrompt} limit={5} />
          <p className="text-xs text-slate-500">누르면 작업실에 문장이 채워집니다.</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <div key={title} className="space-y-2 rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <Icon className="h-5 w-5 text-brand-500" />
            <h2 className="font-semibold text-white">{title}</h2>
            <p className="text-sm text-slate-400">{body}</p>
          </div>
        ))}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-white">어떻게 동작하나요</h2>
        <ol className="grid gap-3 sm:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <li key={title} className="flex gap-3 rounded-2xl border border-slate-800 p-4">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-sm font-semibold text-brand-100">
                {i + 1}
              </span>
              <div>
                <p className="flex items-center gap-1.5 text-sm font-medium text-slate-100">
                  <Icon className="h-4 w-4 text-slate-400" /> {title}
                </p>
                <p className="mt-1 text-xs text-slate-400">{body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">내 최근 작업</h2>
          {loggedIn && (
            <Link to="/history" className="text-sm text-brand-500 hover:text-brand-100">
              전체 보기 →
            </Link>
          )}
        </div>
        {!loggedIn ? (
          <EmptyBlock title="로그인하면 작업이 저장돼요">
            <p className="max-w-sm text-xs text-slate-500">
              로그인하지 않아도 배경 제거 후 바로 다운로드할 수 있어요. 작업 기록 · 피드백 · 배치는 회원 전용입니다.
            </p>
            <span className="flex gap-3">
              <Link to="/login" className="text-brand-500 hover:text-brand-100">
                로그인
              </Link>
              <Link to="/signup" className="text-slate-300 hover:text-white">
                회원가입
              </Link>
            </span>
          </EmptyBlock>
        ) : jobs && jobs.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {jobs.map((job) => (
              <JobCard key={job.job_id} job={job} />
            ))}
          </div>
        ) : (
          <EmptyBlock title="아직 작업이 없어요">
            <Link to="/studio" className="text-brand-500 hover:text-brand-100">
              첫 작업 시작하기
            </Link>
          </EmptyBlock>
        )}
      </section>
    </div>
  );
}

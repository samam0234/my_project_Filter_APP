/**
 * 홈 (/) — 서비스 소개(원본/결과 데모) · 할 수 있는 것 · 사용 순서 · 빠른 시작 · 최근 작업.
 */
import { ArrowRight, Crosshair, Eraser, Focus, ImageUp, MessageSquareText, Sparkles } from "lucide-react";
import { Link, navigate } from "../router";
import { useJobs } from "../hooks/useApi";
import { useAppStore } from "../store/useAppStore";
import { useAuthStore } from "../store/useAuthStore";
import { ExamplePrompts } from "../components/prompt/ExamplePrompts";
import { JobCard } from "../components/jobs/JobCard";
import { EmptyBlock } from "../components/common/States";
import { buttonClass } from "../components/common/Button";
import { HeroDemo } from "../components/home/HeroDemo";

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
  { icon: ImageUp, title: "사진 올리기", body: "JPEG · PNG · WebP, 최대 20MB. 짧은 영상도 돼요." },
  { icon: MessageSquareText, title: "한 문장으로 요청", body: "무엇을 · 어떤 것을 · 어떻게 — 평소 말투 그대로." },
  { icon: Sparkles, title: "결과 받기", body: "원본과 나란히 비교하고 바로 내려받아요." },
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
    <div className="space-y-20">
      <section className="grid grid-cols-1 items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        <div className="space-y-6">
          <p className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-200">
            <Sparkles className="h-3.5 w-3.5" /> 문장 한 줄로 하는 사진 편집
          </p>
          <h1 className="text-4xl font-extrabold leading-[1.15] text-white sm:text-5xl lg:text-[3.4rem]">
            말로 하면,
            <br />
            <span className="bg-gradient-to-r from-brand-300 via-brand-400 to-sky-200 bg-clip-text text-transparent">
              원하는 것만
            </span>{" "}
            남깁니다
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-slate-400">
            사진을 올리고 한 문장으로 요청하세요. 사람·사물을 찾아 배경을 지우거나, 여러 명 중 특정 한 명만
            남기거나, 필요 없는 대상을 지워 드립니다.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/studio" className={buttonClass("primary", "lg")}>
              작업 시작하기 <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/guide" className={buttonClass("secondary", "lg")}>
              프롬프트 쓰는 법
            </Link>
          </div>
          <p className="text-xs text-slate-500">로그인 없이 바로 써 볼 수 있어요 · 결과는 바로 내려받기</p>
        </div>
        <HeroDemo />
      </section>

      <section className="card space-y-3 p-5 sm:p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-base font-semibold text-white">이렇게 말해 보세요</h2>
          <p className="text-xs text-slate-500">누르면 작업실에 문장이 채워집니다.</p>
        </div>
        <ExamplePrompts onPick={tryPrompt} limit={6} />
      </section>

      <section className="space-y-6">
        <div className="space-y-2">
          <p className="eyebrow">할 수 있는 것</p>
          <h2 className="text-2xl font-bold text-white">지우고, 고르고, 남기기</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title} className="card card-hover space-y-3 p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 ring-1 ring-inset ring-brand-500/25">
                <Icon className="h-5 w-5 text-brand-400" />
              </span>
              <h3 className="font-semibold text-white">{title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-6">
        <div className="space-y-2">
          <p className="eyebrow">사용 순서</p>
          <h2 className="text-2xl font-bold text-white">세 단계면 끝나요</h2>
        </div>
        <ol className="relative grid gap-4 sm:grid-cols-3">
          {/* 단계 사이 연결선 (넓은 화면) */}
          <span
            aria-hidden="true"
            className="absolute left-[16%] right-[16%] top-7 hidden h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent sm:block"
          />
          {STEPS.map(({ icon: Icon, title, body }, i) => (
            <li key={title} className="relative flex flex-col items-center gap-3 px-4 text-center">
              <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-700 bg-slate-900 shadow-card">
                <Icon className="h-6 w-6 text-brand-400" />
                <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white ring-4 ring-slate-950">
                  {i + 1}
                </span>
              </span>
              <p className="font-semibold text-slate-100">{title}</p>
              <p className="text-sm text-slate-400">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-5">
        <div className="flex items-end justify-between gap-2">
          <h2 className="text-xl font-bold text-white">내 최근 작업</h2>
          {loggedIn && (
            <Link to="/account?tab=history" className="text-sm text-brand-400 hover:text-brand-200">
              전체 보기 →
            </Link>
          )}
        </div>
        {!loggedIn ? (
          <EmptyBlock title="로그인하면 작업이 저장돼요">
            <p className="max-w-sm text-xs leading-relaxed text-slate-500">
              로그인하지 않아도 배경 제거(사진·영상) 후 바로 다운로드할 수 있어요. 작업 기록 · 피드백 · 배치는 회원 전용입니다.
            </p>
            <span className="mt-1 flex gap-2">
              <Link to="/login" className={buttonClass("secondary", "sm")}>
                로그인
              </Link>
              <Link to="/signup" className={buttonClass("primary", "sm")}>
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
            <Link to="/studio" className={buttonClass("primary", "sm")}>
              첫 작업 시작하기
            </Link>
          </EmptyBlock>
        )}
      </section>
    </div>
  );
}

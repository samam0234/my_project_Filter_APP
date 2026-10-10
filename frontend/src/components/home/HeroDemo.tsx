/**
 * 홈 히어로의 원본/결과 비교 데모.
 *
 * 실제 사진 대신 SVG 일러스트를 쓴다 — 사진 저작권·초상권 걱정이 없고 가볍다.
 * 세 가지 요청(배경 제거 · 대상 지우기 · 배경 블러)을 탭으로 바꿔 보고, 가운데 손잡이를 끌어 원본과 결과를 비교한다.
 * 손잡이는 <input type="range"> 라 키보드(←/→)와 스크린 리더로도 움직일 수 있다.
 */
import { useId, useState } from "react";
import { ChevronsLeftRight } from "lucide-react";

type Layer = "bg" | "left" | "right" | "dog";
type Mode = "show" | "hide" | "blur";

interface Demo {
  prompt: string;
  label: string;
  result: Record<Layer, Mode>;
  checker: boolean;
}

const DEMOS: Demo[] = [
  {
    prompt: "강아지만 남기고 배경 제거",
    label: "배경 제거",
    result: { bg: "hide", left: "hide", right: "hide", dog: "show" },
    checker: true,
  },
  {
    prompt: "왼쪽 사람 지워줘",
    label: "대상 지우기",
    result: { bg: "show", left: "hide", right: "show", dog: "show" },
    checker: false,
  },
  {
    prompt: "사람만 남기고 배경 블러",
    label: "배경 블러",
    result: { bg: "blur", left: "show", right: "show", dog: "blur" },
    checker: false,
  },
];

const ORIGINAL: Record<Layer, Mode> = { bg: "show", left: "show", right: "show", dog: "show" };

function Scene({ modes, blurId }: { modes: Record<Layer, Mode>; blurId: string }) {
  const g = (layer: Layer) =>
    modes[layer] === "hide"
      ? { display: "none" as const }
      : modes[layer] === "blur"
        ? { filter: `url(#${blurId})` }
        : {};
  return (
    <svg viewBox="0 0 400 300" className="block h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id={`${blurId}-sky`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#7dd3fc" />
          <stop offset="1" stopColor="#e0f2fe" />
        </linearGradient>
        <filter id={blurId} x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="5" />
        </filter>
      </defs>

      {/* 블러일 때 가장자리가 투명하게 번지지 않도록 흐리지 않은 하늘·땅을 먼저 깐다 */}
      {modes.bg === "blur" && (
        <>
          <rect width="400" height="300" fill={`url(#${blurId}-sky)`} />
          <rect y="215" width="400" height="85" fill="#4ade80" />
        </>
      )}

      {/* 배경 — 하늘 · 해 · 언덕 · 나무 · 건물 */}
      <g style={g("bg")}>
        <rect width="400" height="300" fill={`url(#${blurId}-sky)`} />
        <circle cx="330" cy="62" r="26" fill="#fde68a" />
        <rect x="24" y="118" width="46" height="110" rx="3" fill="#94a3b8" />
        <rect x="74" y="146" width="34" height="82" rx="3" fill="#a5b4c8" />
        {[0, 1, 2, 3].map((r) =>
          [0, 1].map((c) => (
            <rect key={`${r}-${c}`} x={32 + c * 18} y={130 + r * 22} width="10" height="12" rx="1" fill="#e2e8f0" opacity="0.8" />
          )),
        )}
        <path d="M0 220 Q 90 180 190 214 T 400 200 V300 H0Z" fill="#86efac" />
        <path d="M0 246 Q 120 222 240 246 T 400 238 V300 H0Z" fill="#4ade80" />
        <rect x="352" y="168" width="8" height="52" rx="2" fill="#92400e" />
        <circle cx="356" cy="160" r="24" fill="#22c55e" />
      </g>

      {/* 왼쪽 사람 */}
      <g style={g("left")}>
        <circle cx="128" cy="150" r="15" fill="#fcd34d" />
        <rect x="111" y="168" width="34" height="58" rx="12" fill="#f43f5e" />
        <rect x="114" y="222" width="11" height="36" rx="5" fill="#334155" />
        <rect x="131" y="222" width="11" height="36" rx="5" fill="#334155" />
      </g>

      {/* 오른쪽 사람 */}
      <g style={g("right")}>
        <circle cx="200" cy="140" r="16" fill="#fdba74" />
        <rect x="181" y="159" width="38" height="64" rx="13" fill="#6366f1" />
        <rect x="184" y="219" width="12" height="40" rx="5" fill="#1e293b" />
        <rect x="204" y="219" width="12" height="40" rx="5" fill="#1e293b" />
      </g>

      {/* 강아지 */}
      <g style={g("dog")}>
        <ellipse cx="280" cy="236" rx="34" ry="18" fill="#d97706" />
        <circle cx="314" cy="216" r="15" fill="#d97706" />
        <ellipse cx="324" cy="206" rx="6" ry="10" fill="#92400e" transform="rotate(25 324 206)" />
        <circle cx="319" cy="214" r="2.2" fill="#1c1917" />
        <circle cx="328" cy="221" r="2.6" fill="#1c1917" />
        <rect x="256" y="246" width="8" height="18" rx="3" fill="#b45309" />
        <rect x="292" y="246" width="8" height="18" rx="3" fill="#b45309" />
        <path d="M247 228 q -14 -10 -10 -24" stroke="#d97706" strokeWidth="6" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
}

export function HeroDemo() {
  const [index, setIndex] = useState(0);
  const [pos, setPos] = useState(55);
  const id = useId().replace(/:/g, "");
  const demo = DEMOS[index];

  return (
    <div className="card overflow-hidden p-3 sm:p-4">
      <div role="tablist" aria-label="데모 요청" className="mb-3 flex gap-1 rounded-xl bg-slate-950/60 p-1">
        {DEMOS.map((d, i) => (
          <button
            key={d.label}
            type="button"
            role="tab"
            aria-selected={i === index}
            onClick={() => setIndex(i)}
            className={`flex-1 rounded-lg px-2 py-1.5 text-xs font-medium transition sm:text-sm ${
              i === index ? "bg-slate-800 text-white shadow-card" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="relative aspect-[4/3] select-none overflow-hidden rounded-xl ring-1 ring-slate-800">
        {/* 아래: 결과 */}
        <div className={`absolute inset-0 ${demo.checker ? "bg-checker" : "bg-slate-900"}`}>
          <Scene modes={demo.result} blurId={`${id}-r`} />
        </div>
        {/* 위: 원본 (손잡이 왼쪽만 보임) */}
        <div className="absolute inset-0" style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}>
          <Scene modes={ORIGINAL} blurId={`${id}-o`} />
        </div>

        <span className="pointer-events-none absolute left-2 top-2 rounded-md bg-slate-950/70 px-2 py-0.5 text-[11px] font-medium text-slate-200 backdrop-blur">
          원본
        </span>
        <span className="pointer-events-none absolute right-2 top-2 rounded-md bg-brand-600/90 px-2 py-0.5 text-[11px] font-medium text-white">
          결과
        </span>

        {/* 손잡이 */}
        <div className="pointer-events-none absolute inset-y-0" style={{ left: `${pos}%` }}>
          <div className="absolute inset-y-0 -ml-px w-0.5 bg-white/90 shadow-[0_0_12px_rgba(0,0,0,0.5)]" />
          <div className="absolute top-1/2 -ml-4 -mt-4 flex h-8 w-8 items-center justify-center rounded-full bg-white text-slate-900 shadow-lg">
            <ChevronsLeftRight className="h-4 w-4" />
          </div>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={pos}
          onChange={(e) => setPos(Number(e.target.value))}
          aria-label="원본과 결과 비교 위치"
          className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
        />
      </div>

      <p className="mt-3 flex items-center gap-2 text-sm text-slate-300">
        <span className="rounded-md bg-slate-800 px-1.5 py-0.5 text-[11px] text-slate-400">요청</span>
        “{demo.prompt}”
      </p>
    </div>
  );
}

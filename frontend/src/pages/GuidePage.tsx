/**
 * 프롬프트 가이드 (/guide) — 문장 쓰는 법 · 고르는 조건 · 지원 대상 · 한계 · 예시.
 *
 * 내용은 backend/app/services/prompt_spec.py (규격) 와 instance_selector.py (선택 규칙) 를 따른다.
 */
import { ArrowRight } from "lucide-react";
import { PageHeader } from "../components/common/PageHeader";
import { EXAMPLES, GROUP_LABELS } from "../data/examples";
import { navigate } from "../router";
import { useAppStore } from "../store/useAppStore";

const KEEP_VS_REMOVE = [
  { say: "강아지만 남기고 배경 제거", result: "강아지만 남고 배경은 투명 (PNG)" },
  { say: "강아지만 남기고 배경 블러 강도 40", result: "강아지는 선명, 배경은 흐리게" },
  { say: "강아지만 크롭해줘", result: "강아지 주변으로 잘라낸 사진" },
  { say: "사람 빼고 다 지워줘", result: "사람만 남김 (“빼고/제외하고” = 남기기)" },
  { say: "강아지 지워줘", result: "강아지를 지우고 주변 배경으로 메움" },
];

const SELECTORS = [
  { what: "위치", words: "맨 앞 · 맨 뒤 · 왼쪽 · 오른쪽 · 가운데", how: "앞 = 사진 아래쪽에 있고 크게 보이는 것" },
  { what: "크기", words: "가장 큰 · 가장 작은", how: "화면에서 차지하는 면적" },
  { what: "순서", words: "왼쪽에서 두 번째 · 오른쪽에서 세 번째", how: "위치 기준으로 줄 세운 뒤 N번째" },
  { what: "개수", words: "두 명 · 3마리 · 한 대", how: "숫자를 말하면 그만큼 (위치 없으면 큰 순서)" },
  {
    what: "색 · 부위",
    words: "빨간 안전모 · 형광 조끼 · 파란 셔츠 · 흰색 차",
    how: "대상 영역의 색 비율로 판별 (모자=위쪽, 조끼·셔츠=가운데, 바지=아래)",
  },
];

const LIMITS = [
  "로그인하지 않으면 결과를 서버에 저장하지 않아요 — 처리 직후 내려받으세요. 작업 기록 · 피드백 · 배치는 회원 전용입니다.",
  "지금 서빙 중인 인식 모델은 사람 · 개 · 고양이 · 자동차 · 가방 5종을 압니다. 다른 대상은 “찾지 못했습니다”로 안내돼요.",
  "색은 조명·그림자에 따라 틀릴 수 있어요. 위치와 함께 말하면 더 정확합니다.",
  "지운 자리는 주변 색으로 메우는 방식이라 큰 물체일수록 번진 자국이 남을 수 있어요.",
  "사람이 서로 겹쳐 있으면 경계에 옆 사람 조각이 조금 섞일 수 있어요.",
  "“키 큰 사람”, “웃고 있는 사람”처럼 색·위치 밖의 조건은 아직 이해하지 못해요.",
];

export function GuidePage() {
  const setPrompt = useAppStore((s) => s.setPrompt);
  const tryIt = (text: string) => {
    setPrompt(text);
    navigate("/studio");
  };

  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="프롬프트 가이드"
        title="이렇게 말하면 잘 알아들어요"
        description="한 문장에 “무엇을” + “어떤 것을” + “어떻게” 를 담으면 됩니다."
      />

      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
        <p className="text-sm text-slate-300">
          <span className="rounded bg-brand-500/15 px-1.5 py-0.5 text-brand-100">맨 앞에 빨간 안전모 쓴</span>{" "}
          <span className="rounded bg-slate-700/60 px-1.5 py-0.5 text-slate-100">남자</span>
          <span className="text-slate-400">만 </span>
          <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-emerald-200">남기고 배경 제거</span>
        </p>
        <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-3">
          <p><span className="text-brand-100">어떤 것을</span> — 위치 · 순서 · 개수 · 색 (선택)</p>
          <p><span className="text-slate-100">무엇을</span> — 사람, 강아지, 자동차 …</p>
          <p><span className="text-emerald-200">어떻게</span> — 남기기(배경 제거·블러·크롭) 또는 지우기</p>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">남기기 vs 지우기</h2>
        <div className="overflow-hidden rounded-2xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-xs text-slate-400">
              <tr>
                <th className="px-4 py-2 font-medium">이렇게 말하면</th>
                <th className="px-4 py-2 font-medium">결과</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {KEEP_VS_REMOVE.map((row) => (
                <tr key={row.say}>
                  <td className="px-4 py-2 text-slate-100">“{row.say}”</td>
                  <td className="px-4 py-2 text-slate-400">{row.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500">
          “배경”을 지우라는 말은 대상을 <b className="text-slate-300">남기는</b> 요청이고, 대상 이름을 지우라고 하면 그 대상을{" "}
          <b className="text-slate-300">지웁니다</b>.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">여러 개 중 특정한 것 고르기</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {SELECTORS.map((s) => (
            <div key={s.what} className="space-y-1 rounded-2xl border border-slate-800 p-4">
              <p className="text-sm font-medium text-white">{s.what}</p>
              <p className="text-sm text-brand-100">{s.words}</p>
              <p className="text-xs text-slate-400">{s.how}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          조건이 없으면 같은 종류는 <b className="text-slate-300">전부</b> 대상이 됩니다. 조건끼리는 함께 쓸 수 있어요 — 색으로
          후보를 좁힌 뒤 위치로 줄 세우고 개수만큼 고릅니다.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">예시 — 눌러서 바로 써 보기</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.text}
              type="button"
              onClick={() => tryIt(ex.text)}
              className="group flex items-center gap-3 rounded-xl border border-slate-800 px-4 py-3 text-left transition hover:border-brand-600/60 hover:bg-slate-900"
            >
              <span className="shrink-0 rounded-md bg-slate-800 px-2 py-0.5 text-[11px] text-slate-400">
                {GROUP_LABELS[ex.group]}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm text-slate-100">{ex.text}</span>
                <span className="block text-xs text-slate-500">{ex.point}</span>
              </span>
              <ArrowRight className="h-4 w-4 shrink-0 text-slate-600 group-hover:text-brand-500" />
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">알아 두면 좋은 한계</h2>
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-400">
          {LIMITS.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <p className="text-xs text-slate-500">
          결과가 의도와 다르면 결과 아래 <b className="text-slate-300">정답 알려주기</b>로 원래 의도를 보내 주세요. 문장
          해석 모델을 다시 학습하는 데 쓰입니다.
        </p>
      </section>
    </div>
  );
}

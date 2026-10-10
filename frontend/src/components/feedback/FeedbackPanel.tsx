/**
 * 결과 평가 패널 — 좋아요 / 싫어요 + "정답 알려주기".
 *
 * 싫어요 옆 "정답 알려주기" 는 서버 해석(ParsedPrompt)을 미리 채운 폼을 열고,
 * 사용자가 고친 값을 ParsedPrompt JSON 으로 dislike comment 에 실어 보낸다.
 * → training/lora/dataset.comment_as_parsed 가 이 JSON 을 LoRA 학습 정답으로 쓴다.
 */
import { useMemo, useState } from "react";
import { Check, PencilLine, ThumbsDown, ThumbsUp } from "lucide-react";
import { Button } from "../common/Button";
import { useFeedback } from "../../hooks/useFeedback";
import type { Effect, ParsedPrompt, Position } from "../../types";
import { EFFECT_LABELS, POSITION_LABELS } from "../../utils/formatters";

const COMMON_CLASSES = [
  "person", "dog", "cat", "car", "bus", "truck", "bicycle", "motorcycle", "bird", "horse",
  "cup", "bottle", "chair", "laptop", "cell phone", "handbag", "backpack",
  // 배경 덩어리
  "building", "sky", "road", "sidewalk", "tree", "grass", "water", "mountain", "wall", "floor",
];

interface Draft {
  target: string;
  effect: Effect;
  intensity: number;
  crop: boolean;
  position: Position | "";
  rank: string;
  count: string;
  attributes: string;
}

function toDraft(parsed?: ParsedPrompt | null): Draft {
  const s = parsed?.selector;
  return {
    target: (parsed?.target ?? ["person"]).join(", "),
    effect: ((parsed?.effect as Effect) ?? "remove_bg") || "remove_bg",
    intensity: parsed?.intensity ?? 15,
    crop: Boolean(parsed?.crop),
    position: (s?.position as Position) ?? "",
    rank: s?.rank ? String(s.rank) : "",
    count: s?.count ? String(s.count) : "",
    attributes: (s?.attributes ?? []).join(", "),
  };
}

/** 폼 값 → 서버 정답 형식 (prompt_spec.parsed_to_json 과 같은 키) */
function toParsed(d: Draft): ParsedPrompt {
  const split = (v: string) =>
    v.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
  const num = (v: string) => (v.trim() ? Math.max(1, Math.min(50, Number(v) || 1)) : null);
  const attributes = split(d.attributes);
  const hasSelector = d.position || d.rank || d.count || attributes.length;
  return {
    target: split(d.target),
    effect: d.effect,
    intensity: Math.max(0, Math.min(100, Number(d.intensity) || 0)),
    crop: d.crop || d.effect === "crop",
    selector: hasSelector
      ? {
          position: d.position || null,
          rank: num(d.rank),
          count: num(d.count),
          attributes,
        }
      : null,
  };
}

const field =
  "w-full rounded-lg border border-slate-700/80 bg-slate-950/60 px-2.5 py-1.5 text-sm text-slate-100 outline-none transition hover:border-slate-600 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

interface Props {
  jobId: string;
  parsed?: ParsedPrompt | null;
}

export function FeedbackPanel({ jobId, parsed }: Props) {
  const { vote, message, loading, sent } = useFeedback(jobId);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Draft>(() => toDraft(parsed));
  const corrected = useMemo(() => toParsed(draft), [draft]);
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) =>
    setDraft((d) => ({ ...d, [key]: value }));

  const submitCorrection = async () => {
    if (!corrected.target.length) return;
    const ok = await vote("dislike", JSON.stringify(corrected));
    if (ok) setOpen(false);
  };

  return (
    <div className="space-y-3 card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-1 text-sm text-slate-300">결과가 마음에 드나요?</span>
        <Button variant="secondary" disabled={loading} onClick={() => void vote("like")}>
          <ThumbsUp className="h-4 w-4" /> 좋아요
        </Button>
        <Button variant="secondary" disabled={loading} onClick={() => void vote("dislike")}>
          <ThumbsDown className="h-4 w-4" /> 싫어요
        </Button>
        <Button variant="ghost" disabled={loading} onClick={() => setOpen((v) => !v)}>
          <PencilLine className="h-4 w-4" /> 정답 알려주기
        </Button>
        {message && (
          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
            {sent && <Check className="h-3.5 w-3.5 text-emerald-400" />} {message}
          </span>
        )}
      </div>

      {open && (
        <div className="space-y-3 border-t border-slate-800 pt-3">
          <p className="text-xs text-slate-400">
            원래 의도를 적어 주세요. 이 정답은 프롬프트 해석 모델(LoRA) 재학습에 쓰입니다.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1 text-xs text-slate-400">
              대상 (영어 이름, 쉼표로 여러 개 — 건물은 building)
              <input
                className={field}
                list="coco-classes"
                value={draft.target}
                onChange={(e) => set("target", e.target.value)}
              />
              <datalist id="coco-classes">
                {COMMON_CLASSES.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </label>
            <label className="space-y-1 text-xs text-slate-400">
              하고 싶은 것
              <select
                className={field}
                value={draft.effect}
                onChange={(e) => set("effect", e.target.value as Effect)}
              >
                {(Object.keys(EFFECT_LABELS) as Effect[]).map((k) => (
                  <option key={k} value={k}>
                    {k === "remove_object" ? "대상 지우기" : `대상 남기고 ${EFFECT_LABELS[k]}`}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-xs text-slate-400">
              어느 것 (위치)
              <select
                className={field}
                value={draft.position}
                onChange={(e) => set("position", e.target.value as Position | "")}
              >
                <option value="">전부 (위치 조건 없음)</option>
                {(Object.keys(POSITION_LABELS) as Position[]).map((k) => (
                  <option key={k} value={k}>
                    {POSITION_LABELS[k]}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="space-y-1 text-xs text-slate-400">
                몇 번째
                <input
                  className={field}
                  type="number"
                  min={1}
                  placeholder="1"
                  value={draft.rank}
                  onChange={(e) => set("rank", e.target.value)}
                />
              </label>
              <label className="space-y-1 text-xs text-slate-400">
                개수
                <input
                  className={field}
                  type="number"
                  min={1}
                  placeholder="전부"
                  value={draft.count}
                  onChange={(e) => set("count", e.target.value)}
                />
              </label>
            </div>
            <label className="space-y-1 text-xs text-slate-400 sm:col-span-2">
              색 · 부위 (영어, 쉼표로 여러 개 — 예: red helmet, neon yellow vest, white car)
              <input
                className={field}
                value={draft.attributes}
                onChange={(e) => set("attributes", e.target.value)}
              />
            </label>
            {draft.effect === "blur" && (
              <label className="space-y-1 text-xs text-slate-400">
                블러 강도 ({draft.intensity})
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={draft.intensity}
                  onChange={(e) => set("intensity", Number(e.target.value))}
                  className="w-full accent-brand-500"
                />
              </label>
            )}
            {draft.effect !== "crop" && draft.effect !== "remove_object" && (
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={draft.crop}
                  onChange={(e) => set("crop", e.target.checked)}
                  className="accent-brand-500"
                />
                효과 뒤 대상 주변으로 크롭
              </label>
            )}
          </div>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-2 text-[11px] text-slate-500">
            {JSON.stringify(corrected)}
          </pre>
          <div className="flex gap-2">
            <Button disabled={loading || !corrected.target.length} onClick={() => void submitCorrection()}>
              정답 보내기
            </Button>
            <Button variant="ghost" onClick={() => setDraft(toDraft(parsed))}>
              되돌리기
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

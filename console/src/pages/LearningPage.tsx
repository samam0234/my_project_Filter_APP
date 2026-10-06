/**
 * 학습 데이터 검수 (학습 DB learning_samples).
 *
 * - 승인(approved)된 문장 샘플만 RAG 예시 · LoRA 학습에 쓰인다 → 잘못된 교정이 퍼지는 것을 막는 관문
 * - 정답 수정 후 승인 / 거절 / 삭제(원본 사이드카 파일까지) / 선택 일괄 승인·거절
 * - 출처: correction(정답 알려주기) · like · request(회원 요청 + 시스템 해석) · pipeline_failure · pseudo_label
 */
import { useCallback, useEffect, useState } from "react";
import { Check, Pencil, RotateCcw, Trash2, X } from "lucide-react";
import {
  bulkReview,
  deleteSample,
  errorMessage,
  fetchLearningStats,
  fetchSamples,
  resolveAssetUrl,
  reviewSample,
  type SampleQuery,
} from "../api/client";
import { StatCard } from "../components/StatCard";
import type { LearningSample, LearningStats } from "../types";

const PAGE = 50;

const SOURCE_LABEL: Record<string, string> = {
  correction: "사용자 교정",
  like: "좋아요",
  request: "회원 요청",
  pipeline_failure: "처리 실패",
  pseudo_label: "의사 라벨",
};

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-slate-800 text-slate-200",
  approved: "bg-emerald-900/50 text-emerald-300",
  rejected: "bg-rose-900/40 text-rose-300",
};

/** 정답 JSON 한 줄 요약 */
function summarize(answer?: Record<string, unknown> | null): string {
  if (!answer) return "-";
  const sel = (answer.selector || {}) as Record<string, unknown>;
  const parts = [
    `${(answer.target as string[] | undefined)?.join(",") ?? "?"} · ${answer.effect ?? "?"}`,
    sel.position ? `위치 ${sel.position}` : "",
    sel.rank ? `${sel.rank}번째` : "",
    sel.count ? `${sel.count}개` : "",
    Array.isArray(sel.attributes) && sel.attributes.length ? `속성 ${sel.attributes.join("/")}` : "",
    answer.crop ? "crop" : "",
  ];
  return parts.filter(Boolean).join(" · ");
}

export function LearningPage() {
  // 기본은 사용자 데이터(교정·좋아요·회원 요청) — 의사 라벨 수천 건에 묻히지 않게
  const [query, setQuery] = useState<SampleQuery>({ status: "pending", source: "user", kind: "prompt", q: "" });
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState<LearningSample[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editing, setEditing] = useState<{ id: string; text: string; note: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const [list, st] = await Promise.all([
        fetchSamples({ ...query, limit: PAGE, offset }),
        fetchLearningStats(),
      ]);
      setItems(list.items);
      setTotal(list.total);
      setStats(st);
      setSelected(new Set());
    } catch (err) {
      setMessage(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }, [query, offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (fn: () => Promise<unknown>, done: string) => {
    setBusy(true);
    try {
      await fn();
      setMessage(done);
      setEditing(null);
      await load();
    } catch (err) {
      setMessage(errorMessage(err));
      setBusy(false);
    }
  };

  const saveEdit = () => {
    if (!editing) return;
    let answer: Record<string, unknown>;
    try {
      answer = JSON.parse(editing.text);
    } catch {
      setMessage("정답이 올바른 JSON 이 아닙니다.");
      return;
    }
    void run(() => reviewSample(editing.id, "approve", answer, editing.note), "정답을 고쳐 승인했습니다.");
  };

  const setFilter = (patch: Partial<SampleQuery>) => {
    setOffset(0);
    setQuery((q) => ({ ...q, ...patch }));
  };

  const toggle = (id: string) =>
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const by = stats?.by_status ?? {};
  const split = stats?.approved_by_split ?? {};

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">학습 데이터 검수</h2>
        <p className="mt-1 text-sm text-console-muted">
          승인한 문장만 프롬프트 RAG 예시와 LoRA 학습에 쓰입니다. 잘못된 교정은 거절하거나 정답을 고쳐 승인하세요.
          {stats?.learning_db && <> · 학습 DB: <span className="text-slate-300">{stats.learning_db}</span></>}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="검수 대기" value={by.pending ?? 0} />
        <StatCard
          label="승인"
          value={by.approved ?? 0}
          hint={`train ${split.train ?? 0} · val ${split.val ?? 0} · 재학습 ${stats?.approved_user_prompts ?? 0}/${stats?.retrain_min_new ?? 200}`}
        />
        <StatCard label="거절" value={by.rejected ?? 0} />
        <StatCard
          label="사용자 데이터 대기"
          value={
            (stats?.by_source.request?.pending ?? 0) +
            (stats?.by_source.like?.pending ?? 0) +
            (stats?.by_source.correction?.pending ?? 0)
          }
          hint={`교정 ${stats?.by_source.correction?.pending ?? 0} · 좋아요 ${stats?.by_source.like?.pending ?? 0} · 요청 ${stats?.by_source.request?.pending ?? 0}`}
        />
      </div>

      {/* 필터 */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-console-border bg-console-panel p-3 text-sm">
        <label className="flex flex-col gap-1 text-xs text-console-muted">
          상태
          <select
            className="rounded-lg border border-console-border bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
            value={query.status}
            onChange={(e) => setFilter({ status: e.target.value })}
          >
            <option value="pending">검수 대기</option>
            <option value="approved">승인</option>
            <option value="rejected">거절</option>
            <option value="">전체</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-console-muted">
          출처
          <select
            className="rounded-lg border border-console-border bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
            value={query.source}
            onChange={(e) => setFilter({ source: e.target.value })}
          >
            <option value="user">사용자 데이터 (교정·좋아요·요청)</option>
            <option value="">전체</option>
            {Object.entries(SOURCE_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-console-muted">
          종류
          <select
            className="rounded-lg border border-console-border bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
            value={query.kind}
            onChange={(e) => setFilter({ kind: e.target.value })}
          >
            <option value="prompt">문장 (LoRA·RAG)</option>
            <option value="segment">세그 실패 이미지</option>
            <option value="">전체</option>
          </select>
        </label>
        <label className="flex min-w-48 flex-1 flex-col gap-1 text-xs text-console-muted">
          문장 검색
          <input
            className="rounded-lg border border-console-border bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
            placeholder="예: 왼쪽 두 번째"
            defaultValue={query.q}
            onKeyDown={(e) => e.key === "Enter" && setFilter({ q: (e.target as HTMLInputElement).value })}
          />
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy || selected.size === 0}
            onClick={() =>
              void run(async () => {
                const r = await bulkReview([...selected], "approve");
                if (r.skipped.length) throw new Error(`${r.done}건 승인, ${r.skipped.length}건 건너뜀 (정답 없음)`);
              }, `${selected.size}건 승인했습니다.`)
            }
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-white disabled:opacity-40"
          >
            선택 승인 ({selected.size})
          </button>
          <button
            type="button"
            disabled={busy || selected.size === 0}
            onClick={() => void run(() => bulkReview([...selected], "reject"), `${selected.size}건 거절했습니다.`)}
            className="rounded-lg bg-rose-700 px-3 py-1.5 text-white disabled:opacity-40"
          >
            선택 거절
          </button>
        </div>
      </div>

      {message && (
        <div className="flex items-center justify-between rounded-xl border border-console-border bg-slate-900 px-4 py-2 text-sm text-slate-200">
          {message}
          <button type="button" onClick={() => setMessage(null)} className="text-console-muted">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-console-border bg-console-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-xs uppercase text-console-muted">
              <tr>
                <th className="px-3 py-3">
                  <input
                    type="checkbox"
                    aria-label="전체 선택"
                    checked={items.length > 0 && selected.size === items.length}
                    onChange={(e) => setSelected(e.target.checked ? new Set(items.map((i) => i.id)) : new Set())}
                  />
                </th>
                <th className="px-3 py-3">문장</th>
                <th className="px-3 py-3">정답 (해석)</th>
                <th className="px-3 py-3">출처</th>
                <th className="px-3 py-3">상태</th>
                <th className="px-3 py-3">이미지</th>
                <th className="px-3 py-3">작업</th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.id} className="border-t border-console-border align-top">
                  <td className="px-3 py-3">
                    <input type="checkbox" checked={selected.has(s.id)} onChange={() => toggle(s.id)} />
                  </td>
                  <td className="max-w-xs px-3 py-3 text-slate-100">
                    {s.prompt || <span className="text-console-muted">(문장 없음)</span>}
                    <div className="mt-1 text-xs text-console-muted">
                      {new Date(s.created_at).toLocaleString("ko-KR")}
                      {s.note && <> · 메모: {s.note}</>}
                    </div>
                  </td>
                  <td className="max-w-sm px-3 py-3">
                    {editing?.id === s.id ? (
                      <div className="space-y-2">
                        <textarea
                          className="h-36 w-80 rounded-lg border border-console-border bg-slate-950 p-2 font-mono text-xs text-slate-100"
                          value={editing.text}
                          onChange={(e) => setEditing({ ...editing, text: e.target.value })}
                        />
                        <input
                          className="w-80 rounded-lg border border-console-border bg-slate-950 px-2 py-1 text-xs text-slate-100"
                          placeholder="메모 (선택)"
                          value={editing.note}
                          onChange={(e) => setEditing({ ...editing, note: e.target.value })}
                        />
                        <div className="flex gap-2">
                          <button type="button" onClick={saveEdit} className="rounded bg-emerald-600 px-2 py-1 text-xs text-white">
                            고쳐서 승인
                          </button>
                          <button type="button" onClick={() => setEditing(null)} className="rounded bg-slate-700 px-2 py-1 text-xs text-white">
                            취소
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-300" title={JSON.stringify(s.answer, null, 2)}>
                        {summarize(s.answer)}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-xs">{SOURCE_LABEL[s.source] ?? s.source}</td>
                  <td className="px-3 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[s.status] ?? ""}`}>
                      {s.status}
                      {s.split ? ` · ${s.split}` : ""}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    {s.has_image && s.image_url ? (
                      <a href={resolveAssetUrl(s.image_url)} target="_blank" rel="noreferrer">
                        <img
                          src={resolveAssetUrl(s.image_url)}
                          alt="원본"
                          className="h-14 w-20 rounded object-cover"
                          loading="lazy"
                        />
                      </a>
                    ) : (
                      <span className="text-xs text-console-muted">-</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {s.status !== "approved" && (
                        <button
                          type="button"
                          title="승인"
                          disabled={busy || !s.answer}
                          onClick={() => void run(() => reviewSample(s.id, "approve"), "승인했습니다.")}
                          className="rounded bg-emerald-700 p-1.5 text-white disabled:opacity-40"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {s.kind === "prompt" && (
                        <button
                          type="button"
                          title="정답 고쳐서 승인"
                          disabled={busy}
                          onClick={() =>
                            setEditing({ id: s.id, text: JSON.stringify(s.answer ?? {}, null, 2), note: s.note ?? "" })
                          }
                          className="rounded bg-sky-700 p-1.5 text-white disabled:opacity-40"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {s.status !== "rejected" && (
                        <button
                          type="button"
                          title="거절"
                          disabled={busy}
                          onClick={() => void run(() => reviewSample(s.id, "reject"), "거절했습니다.")}
                          className="rounded bg-rose-800 p-1.5 text-white disabled:opacity-40"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {s.status !== "pending" && (
                        <button
                          type="button"
                          title="검수 대기로 되돌리기"
                          disabled={busy}
                          onClick={() => void run(() => reviewSample(s.id, "reset"), "검수 대기로 되돌렸습니다.")}
                          className="rounded bg-slate-700 p-1.5 text-white disabled:opacity-40"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <button
                        type="button"
                        title="삭제 (원본 파일 포함)"
                        disabled={busy}
                        onClick={() => {
                          if (window.confirm("이 학습 데이터를 삭제할까요? 원본 사이드카 파일도 지워지고 되돌릴 수 없습니다.")) {
                            void run(() => deleteSample(s.id), "삭제했습니다.");
                          }
                        }}
                        className="rounded bg-slate-800 p-1.5 text-rose-300 disabled:opacity-40"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-10 text-center text-console-muted">
                    {busy ? "불러오는 중…" : "조건에 맞는 학습 데이터가 없습니다."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t border-console-border px-4 py-2 text-xs text-console-muted">
          <span>
            {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE, total)} / {total}건
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0 || busy}
              onClick={() => setOffset((o) => Math.max(0, o - PAGE))}
              className="rounded border border-console-border px-2 py-1 disabled:opacity-40"
            >
              이전
            </button>
            <button
              type="button"
              disabled={offset + PAGE >= total || busy}
              onClick={() => setOffset((o) => o + PAGE)}
              className="rounded border border-console-border px-2 py-1 disabled:opacity-40"
            >
              다음
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

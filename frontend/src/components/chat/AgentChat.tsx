/**
 * 에이전트에게 묻기 — 프롬프트 가이드 안의 AI 채팅.
 *
 * - 서비스 사용법(요청 문장 쓰는 법)을 AI 에게 물어본다. 답에 `백틱`으로 감싼 추천 문장이 있으면
 *   "작업실에서 써 보기" 버튼으로 바로 작업실의 입력 칸에 채운다.
 * - 답하는 모델은 작업실과 같은 목록(설치된 Ollama 모델)에서 고른다. 서버가 Ollama 로 해석하지 않으면 채팅은 꺼진다.
 * - 대화는 서버에 저장되지 않는다 (이 탭의 메모리뿐).
 */
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Bot, Loader2, Send, Trash2, User, Wand2 } from "lucide-react";
import { Button } from "../common/Button";
import { ModelSelect } from "../common/ModelSelect";
import { navigate } from "../../router";
import { useAppStore } from "../../store/useAppStore";
import { useChatStore } from "../../store/useChatStore";
import { useLlmModelStore } from "../../store/useLlmModelStore";

const STARTERS = [
  "배경만 흐리게 하고 싶어요",
  "여러 명 중에 한 명만 고르는 법",
  "빨간 모자 쓴 사람만 남기려면?",
  "건물을 지우면 왜 어색해요?",
];

/** 답변 글 → `백틱` 부분은 눌러 쓸 수 있는 문장 상자로, 나머지는 그대로 */
export function splitReply(text: string): { kind: "text" | "prompt"; value: string }[] {
  const parts: { kind: "text" | "prompt"; value: string }[] = [];
  const re = /`([^`\n]{2,200})`/g;
  let last = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (m.index > last) parts.push({ kind: "text", value: text.slice(last, m.index) });
    parts.push({ kind: "prompt", value: m[1].trim() });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ kind: "text", value: text.slice(last) });
  return parts;
}

function Assistant({ text, onTry }: { text: string; onTry: (prompt: string) => void }) {
  return (
    <div className="space-y-2 whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-200">
      {splitReply(text).map((p, i) =>
        p.kind === "text" ? (
          <span key={i}>{p.value}</span>
        ) : (
          <span key={i} className="my-1 flex flex-wrap items-center gap-2 rounded-xl border border-brand-700/40 bg-brand-900/20 px-3 py-2">
            <code className="min-w-0 flex-1 break-words font-medium text-brand-100">{p.value}</code>
            <button
              type="button"
              onClick={() => onTry(p.value)}
              className="inline-flex shrink-0 items-center gap-1 rounded-lg bg-brand-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-brand-500"
            >
              <Wand2 className="h-3 w-3" /> 작업실에서 써 보기
            </button>
          </span>
        ),
      )}
    </div>
  );
}

export function AgentChat() {
  const { messages, sending, error, send, clear, lastModel } = useChatStore();
  const enabled = useLlmModelStore((s) => s.enabled);
  const loaded = useLlmModelStore((s) => s.loaded);
  const refresh = useLlmModelStore((s) => s.refresh);
  const setPrompt = useAppStore((s) => s.setPrompt);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" });
  }, [messages.length, sending]);

  const tryPrompt = (text: string) => {
    setPrompt(text);
    navigate("/studio");
  };

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    void send(text);
  };
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  if (loaded && !enabled) {
    return (
      <div className="card p-6 text-sm text-slate-300" role="status">
        이 서버는 AI 상담을 지원하지 않아요. (문장 해석이 Ollama 방식일 때만 켜져요.) 위의 <b>일반 가이드</b>를 참고해 주세요.
      </div>
    );
  }

  return (
    <section className="card space-y-4 p-4 sm:p-5" aria-label="에이전트와 채팅">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="flex items-center gap-2 text-base font-semibold text-white">
            <Bot className="h-4 w-4 text-brand-400" /> 에이전트에게 묻기
          </h2>
          <p className="text-xs leading-relaxed text-slate-400">
            원하는 결과를 말하면 알맞은 요청 문장을 만들어 줘요. 대화는 서버에 저장되지 않아요.
          </p>
        </div>
        <div className="flex items-start gap-2">
          <ModelSelect disabled={sending} label="답변 모델" ariaLabel="AI 답변 모델" />
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clear} disabled={sending} aria-label="대화 지우기">
              <Trash2 className="h-3.5 w-3.5" /> 지우기
            </Button>
          )}
        </div>
      </div>

      <div className="max-h-[28rem] min-h-[10rem] space-y-4 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950/40 p-3 sm:p-4" aria-live="polite">
        {messages.length === 0 && (
          <div className="space-y-3 text-sm text-slate-400">
            <p>이런 걸 물어보세요.</p>
            <div className="flex flex-wrap gap-2">
              {STARTERS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => void send(q)}
                  disabled={sending}
                  className="rounded-full border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-brand-500 hover:text-white disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <span
              className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${
                m.role === "user" ? "bg-slate-700" : "bg-brand-500/15 ring-1 ring-inset ring-brand-500/30"
              }`}
              aria-hidden
            >
              {m.role === "user" ? <User className="h-3.5 w-3.5 text-slate-200" /> : <Bot className="h-3.5 w-3.5 text-brand-300" />}
            </span>
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 ${
                m.role === "user" ? "bg-brand-600/90 text-sm text-white" : "bg-slate-900 ring-1 ring-inset ring-slate-800"
              }`}
            >
              {m.role === "user" ? <p className="whitespace-pre-wrap break-words">{m.content}</p> : <Assistant text={m.content} onTry={tryPrompt} />}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-xs text-slate-400" role="status">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-400" /> 답을 만드는 중… (큰 모델은 처음에 오래 걸려요)
          </div>
        )}
        {error && (
          <p role="alert" className="rounded-xl border border-rose-800/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
            {error}
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="flex items-end gap-2">
        <textarea
          aria-label="질문 입력"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          rows={2}
          maxLength={1500}
          placeholder="예: 사진에서 강아지만 남기고 배경을 흐리게 하려면 뭐라고 쓰죠?  (Enter 전송 · Shift+Enter 줄바꿈)"
          className="field min-h-[3rem] flex-1 resize-none"
        />
        <Button type="submit" disabled={sending || !input.trim()} aria-label="보내기">
          <Send className="h-4 w-4" /> 보내기
        </Button>
      </form>
      {lastModel && messages.length > 0 && <p className="text-right text-[11px] text-slate-600">마지막 답변 모델: {lastModel}</p>}
    </section>
  );
}

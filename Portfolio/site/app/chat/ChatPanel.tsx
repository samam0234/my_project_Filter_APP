"use client";

import { useEffect, useRef, useState } from "react";

type Role = "user" | "assistant";
type Msg = { role: Role; content: string; sources?: string[] };
type Health = { ok?: boolean; ready?: boolean; model?: string; detail?: string };
type Quota = { used: number; remaining: number; limit: number; resets: string };

const KEY = "cnk-portfolio-chat-v1";
const prompts = [
  "컷앤킵이 무엇을 하는 서비스인지 짧게 설명해 주세요.",
  "비로그인과 회원이 할 수 있는 일의 차이는 무엇인가요?",
  "문장 해석에 LangChain과 RAG가 어떻게 쓰이나요?",
  "운영 서버가 PC의 Ollama에 의존하는 이유는 무엇인가요?",
  "서비스 DB와 학습 DB는 왜 나뉘어 있나요?",
  "오픈 보캐브는 지금 켜져 있나요?",
];

const pool = [
  ...prompts,
  "YOLO26m-seg와 SegFormer는 각각 무엇을 담당하나요?",
  "영상과 GIF 지우기는 사진 지우기와 어떻게 다른가요?",
  "배치 작업은 누가, 몇 장까지 할 수 있나요?",
  "공개 주소와 Cloudflare Worker의 역할은 무엇인가요?",
  "콘솔은 왜 공개 서버에 올라가 있지 않나요?",
  "이메일 인증 가입은 어떻게 동작하나요?",
  "LangGraph 파이프라인의 단계는 무엇인가요?",
  "승인되지 않은 피드백은 언제 RAG 예시가 되나요?",
  "파일은 얼마나 보관되고, 손님의 결과는 저장되나요?",
  "ARM 서버에서 GPU와 LoRA를 쓰지 않는 이유는 무엇인가요?",
  "Worker가 긴 작업을 끊는 시간은 어느 정도인가요?",
  "앞으로 추가하려는 서버나 기능은 무엇이 있나요?",
  "signup_pending 표는 ERD 그림에 왜 없나요?",
  "제품 기본 모델과 이 안내 챗의 모델은 각각 무엇인가요?",
  "움직이는 카메라 영상의 지우기는 어디까지 되나요?",
];

function pickThree(previous: string[]) {
  const bag = pool.filter((item) => !previous.includes(item));
  const source = bag.length >= 3 ? bag : [...pool];
  const copy = [...source];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, 3);
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [pending, setPending] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [sparks, setSparks] = useState<string[] | null>(null);
  const [quota, setQuota] = useState<Quota | null>(null);
  const [deepOn, setDeepOn] = useState(false);
  const [deepWait, setDeepWait] = useState(false);
  const box = useRef<HTMLTextAreaElement>(null);
  const tools = useRef<HTMLDivElement>(null);

  function loadQuota() {
    fetch("/api/deep")
      .then((res) => res.json())
      .then((data: Quota) => {
        if (typeof data.remaining === "number") setQuota(data);
      })
      .catch(() => setQuota(null));
  }

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Msg[];
        if (Array.isArray(parsed)) setMessages(parsed.slice(-40));
      }
    } catch {
      localStorage.removeItem(KEY);
    }
    setHydrated(true);
    fetch("/api/chat")
      .then((res) => res.json())
      .then((data: Health) => setHealth(data))
      .catch(() => setHealth({ ready: false, detail: "상태 확인에 실패했습니다." }));
    loadQuota();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(KEY, JSON.stringify(messages.slice(-40)));
  }, [messages, hydrated]);

  useEffect(() => {
    if (quota && quota.remaining <= 0) setDeepOn(false);
  }, [quota]);

  useEffect(() => {
    const area = box.current;
    if (!area) return;
    const min = tools.current?.offsetHeight ?? 0;
    const style = getComputedStyle(area);
    const line = Number.parseFloat(style.lineHeight) || 24;
    const pad = Number.parseFloat(style.paddingTop) + Number.parseFloat(style.paddingBottom);
    const border = Number.parseFloat(style.borderTopWidth) + Number.parseFloat(style.borderBottomWidth);
    const max = line * 15 + pad + border;
    area.style.height = "auto";
    const needed = Math.max(area.scrollHeight, min);
    const next = Math.min(needed, max);
    area.style.height = `${next}px`;
    area.style.overflowY = area.scrollHeight > max + 1 ? "auto" : "hidden";
  }, [text]);

  async function send(content: string, deep = false) {
    const question = content.trim();
    if (!question || pending) {
      if (deep && !question) setError("질문을 입력한 뒤 보내기를 누르세요.");
      return;
    }
    const next = [...messages, { role: "user" as const, content: question }];
    setMessages(next);
    setText("");
    setPending(true);
    setDeepWait(deep);
    setError("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          deep,
          messages: next.slice(-8).map(({ role, content: body }) => ({ role, content: body })),
        }),
      });
      const data = (await res.json()) as { answer?: string; sources?: string[]; detail?: string };
      if (deep) loadQuota();
      if (!res.ok) {
        setError(data.detail || "답변을 받지 못했습니다.");
        return;
      }
      setMessages([
        ...next,
        { role: "assistant", content: data.answer || "빈 답변입니다.", sources: data.sources || [] },
      ]);
    } catch {
      if (deep) loadQuota();
      setError("네트워크 오류로 답을 받지 못했습니다. 대화는 이 브라우저에 남아 있습니다.");
    } finally {
      setPending(false);
      setDeepWait(false);
    }
  }

  function clear() {
    setMessages([]);
    localStorage.removeItem(KEY);
  }

  function roll() {
    setSparks((current) => pickThree(current ?? []));
  }

  function useSpark(prompt: string) {
    setText(prompt);
    setSparks(null);
    box.current?.focus();
  }

  return (
    <div className="chat">
      <aside>
        <div className="note">
          {health?.ready
            ? `모델 ${health.model} 이 준비되어 있습니다.`
            : health?.detail || "안내 서비스 상태를 확인하는 중입니다."}
        </div>
        <div className="prompts">
          {prompts.map((prompt) => (
            <button key={prompt} type="button" onClick={() => send(prompt)} disabled={pending}>
              {prompt}
            </button>
          ))}
        </div>
        <div className="actions">
          <button className="btn alt" type="button" onClick={clear}>대화 지우기</button>
        </div>
      </aside>
      <section className="thread">
        <div className="messages" aria-live="polite">
          {messages.length === 0 && (
            <p>
              문서에 있는 내용만 답합니다. 이 창의 기록은 localStorage에 있고, 배운 질문과 답은 JSON에 남습니다.
              뇌 버튼을 누르면 깊이 추론이 선택되고, 보내기가 그 모드로 나갑니다. 이 사이트 전체에서 하루 10번이고, 한국 시간 오전 12시에 초기화됩니다.
              횟수는 서버 SQLite에 있으며 이 브라우저에 저장하지 않습니다.
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={`${msg.role}-${i}`} className={`bubble ${msg.role}`}>
              {msg.content}
              {msg.sources && msg.sources.length > 0 && <small>근거: {msg.sources.join(", ")}</small>}
            </div>
          ))}
          {pending && (
            <div className="bubble assistant typing">
              <span /><span /><span />
              {deepWait
                ? "깊이 추론 중입니다. 문서를 더 넓게 보고, 생성을 일반 답의 2.5배로 씁니다. 5분에서 10분까지 걸릴 수 있습니다."
                : "문서를 찾고 12b로 답을 쓰는 중입니다. 처음이면 모델 로드로 1분 가까이 걸릴 수 있습니다."}
            </div>
          )}
          {error && <div className="note">{error}</div>}
        </div>
        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            void send(text, deepOn);
          }}
        >
          {sparks && (
            <div className="sparks" aria-label="추천 질문">
              {sparks.map((prompt) => (
                <button key={prompt} type="button" onClick={() => useSpark(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          )}
          <div className="composer-row">
            <textarea
              ref={box}
              value={text}
              maxLength={2000}
              placeholder="프로젝트에 대해 질문"
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Escape") setSparks(null);
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send(text, deepOn);
                }
              }}
            />
            <div className="composer-tools" ref={tools}>
              <button
                className="brain"
                type="button"
                aria-label="깊이 추론하기"
                aria-pressed={deepOn}
                title={
                  quota
                    ? `깊이 추론하기. ${deepOn ? "선택됨. 보내기로 전송합니다." : "누르면 선택된 뒤 보내기로 전송합니다."} 오늘 ${quota.remaining}/${quota.limit}. 이 사이트 전체이며 ${quota.resets}에 초기화됩니다.`
                    : "깊이 추론하기. 오늘 남은 횟수를 확인하는 중입니다."
                }
                disabled={pending || !quota || quota.remaining <= 0}
                onClick={() => {
                  setError("");
                  setDeepOn((current) => !current);
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
                  <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
                  <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
                </svg>
                <span className="brain-count">{quota ? `${quota.remaining}/${quota.limit}` : "…"}</span>
              </button>
              <button
                className="bolt"
                type="button"
                aria-label="관련 질문 추천"
                aria-expanded={sparks !== null}
                onClick={roll}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path fill="currentColor" d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" />
                </svg>
              </button>
            </div>
            <button className="btn" type="submit" disabled={pending}>보내기</button>
          </div>
        </form>
      </section>
    </div>
  );
}

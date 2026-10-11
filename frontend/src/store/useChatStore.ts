/**
 * AI 채팅(프롬프트 가이드 "에이전트에게 묻기") 대화 상태 (Zustand).
 *
 * - 대화는 이 브라우저 탭의 메모리에만 둔다 — 서버는 저장하지 않고, 새로고침하면 사라진다 (개인정보를 남기지 않기 위해).
 *   가이드 탭을 오가거나 다른 화면에 다녀와도 유지된다.
 * - 보낼 때 최근 대화 전체를 서버에 함께 보낸다 (서버는 길이 · 개수를 다시 제한).
 * - 모델은 작업실과 같은 선택(useLlmModelStore)을 쓴다.
 */
import { create } from "zustand";
import { errorMessage, sendChat } from "../api/client";
import type { ChatMessage } from "../types";
import { useLlmModelStore } from "./useLlmModelStore";

interface ChatState {
  messages: ChatMessage[];
  sending: boolean;
  error: string | null;
  /** 마지막 답을 만든 모델 (표시용) */
  lastModel: string | null;
  send: (text: string) => Promise<void>;
  clear: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sending: false,
  error: null,
  lastModel: null,

  send: async (text) => {
    const content = text.trim();
    if (!content || get().sending) return;
    const next: ChatMessage[] = [...get().messages, { role: "user", content }];
    set({ messages: next, sending: true, error: null });
    try {
      const model = useLlmModelStore.getState().selected;
      const res = await sendChat(next, model ?? undefined);
      set({ messages: [...get().messages, { role: "assistant", content: res.reply }], lastModel: res.model });
    } catch (err) {
      set({ error: errorMessage(err, "답을 받지 못했어요.") });
    } finally {
      set({ sending: false });
    }
  },

  clear: () => set({ messages: [], error: null, lastModel: null }),
}));

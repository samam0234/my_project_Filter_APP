/**
 * 문장 해석 모델 선택 (Zustand) — 사진 · GIF · 영상 작업실이 하나를 공유한다.
 *
 * - models : 서버(GET /llm/models)가 알려 준 목록과 설치 여부. 설치되지 않은 모델은 available=false → "미적용"
 * - selected : 사용자가 고른 모델 id. null 이면 서버 기본 모델 (요청에 llm_model 을 보내지 않는다)
 * - enabled : 서버가 해석을 Ollama 가 아닌 것(예: GPU 서버의 LoRA)으로 하면 false — 선택 상자를 숨긴다
 *
 * 선택은 이 브라우저에 기억한다 (localStorage — 못 쓰는 환경이면 그냥 메모리에서만).
 * 고른 모델이 나중에 "미적용"이 되거나 목록에서 사라지면 기본 모델로 돌아간다.
 * "미적용"이던 모델은 사용자가 서버에서 내려받으면 다음 조회(창으로 돌아올 때 · 30초마다)에 풀린다.
 */
import { create } from "zustand";
import { getLlmModels } from "../api/client";
import type { LlmModel, LlmModelList } from "../types";

const KEY = "cnk.llmModel";

function readSaved(): string | null {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function save(id: string | null): void {
  try {
    if (id) window.localStorage.setItem(KEY, id);
    else window.localStorage.removeItem(KEY);
  } catch {
    /* 저장소를 못 써도 선택은 이번 방문 동안 유지된다 */
  }
}

interface LlmModelState {
  enabled: boolean;
  loaded: boolean;
  defaultId: string | null;
  models: LlmModel[];
  selected: string | null;

  refresh: () => Promise<void>;
  select: (id: string | null) => void;
}

export const useLlmModelStore = create<LlmModelState>((set, get) => ({
  enabled: false,
  loaded: false,
  defaultId: null,
  models: [],
  selected: readSaved(),

  refresh: async () => {
    let list: LlmModelList;
    try {
      list = await getLlmModels();
    } catch {
      // 서버에 못 닿으면 선택 상자만 숨긴다 — 처리 자체는 기본 모델로 계속된다
      set({ enabled: false, loaded: true });
      return;
    }
    const current = get().selected;
    const usable = current ? list.models.find((m) => m.id === current && m.available) : undefined;
    if (current && !usable) save(null);
    set({
      enabled: list.enabled && list.models.length > 1,
      loaded: true,
      defaultId: list.default,
      models: list.models,
      selected: usable ? current : null,
    });
  },

  select: (id) => {
    save(id);
    set({ selected: id });
  },
}));

/** 요청에 실어 보낼 값 — 기본 모델이면 undefined (서버가 설정 그대로 쓴다) */
export function currentLlmModel(): string | undefined {
  const { selected, defaultId } = useLlmModelStore.getState();
  return selected && selected !== defaultId ? selected : undefined;
}

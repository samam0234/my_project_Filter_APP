/**
 * 처리한 영상 결과를 이 브라우저에 보관 (IndexedDB) — 새로고침·재방문해도 다시 재생하고 저장할 수 있게.
 *
 * localStorage 는 문자열만 담고 용량이 5MB 안팎이라 영상에 쓸 수 없어, 같은 브라우저 로컬 저장소인
 * IndexedDB 에 Blob 을 그대로 넣는다. 마지막 1건만 보관한다 (용량 제한 · 개인 영상이 쌓이지 않게).
 * 서버와는 무관하다 — 비로그인 결과는 서버에 남지 않으므로 이 보관이 유일한 "다시 보기" 수단이다.
 *
 * 시크릿 창·저장소 차단·용량 초과 등으로 어떤 단계든 실패할 수 있어 모든 함수는 예외 대신 null/false 를 돌려준다.
 */
import type { VideoFormat } from "../types";

export interface StoredVideo {
  blob: Blob;
  format: VideoFormat;
  frames: number;
  held: number;
  /** 처리에 쓴 문장 · 원본 파일명 (다시 처리할 때 채워 줌) */
  prompt: string;
  fileName: string;
  /** 서버가 해석한 효과와 요청 강도 */
  effect?: string;
  intensity?: number;
  /** 'guest' 또는 회원 id — 다른 계정이 같은 브라우저를 쓸 때 남의 결과를 보여 주지 않는다 */
  owner: string;
  savedAt: number;
}

const DB_NAME = "cutnkeep";
const STORE = "video";
const KEY = "last";

function open(): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    try {
      if (typeof indexedDB === "undefined") return resolve(null);
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(STORE);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      req.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

async function run<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequest<T>): Promise<T | null> {
  const db = await open();
  if (!db) return null;
  try {
    return await new Promise<T | null>((resolve) => {
      const tx = db.transaction(STORE, mode);
      const req = fn(tx.objectStore(STORE));
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      tx.onabort = () => resolve(null);
    });
  } catch {
    return null;
  } finally {
    db.close();
  }
}

/** 마지막 결과로 저장 (이전 것은 덮어씀). 성공 여부. */
export async function saveVideo(item: StoredVideo): Promise<boolean> {
  return (await run("readwrite", (s) => s.put(item, KEY))) !== null;
}

/** 저장된 마지막 결과. owner 가 다르거나 없으면 null. */
export async function loadVideo(owner: string): Promise<StoredVideo | null> {
  const found = await run<StoredVideo | undefined>("readonly", (s) => s.get(KEY));
  return found && found.owner === owner && found.blob ? found : null;  // 구조화 복제로 Blob 이 그대로 돌아온다
}

export async function clearVideo(): Promise<boolean> {
  return (await run("readwrite", (s) => s.delete(KEY))) !== null;
}

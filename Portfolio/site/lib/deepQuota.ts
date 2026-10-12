/** 안내 서비스가 가진 깊이 추론 횟수. 이 프로세스의 디스크에는 세지 않는다. */

const AI = process.env.PORTFOLIO_AI_URL || "http://127.0.0.1:5055";

export type DeepQuota = {
  ok: boolean;
  limit: number;
  used: number;
  remaining: number;
  resets: string;
  date: string;
  detail?: string;
};

const UNKNOWN: DeepQuota = {
  ok: false,
  limit: 10,
  used: 0,
  remaining: 0,
  resets: "한국 시간 오전 12시",
  date: "",
  detail: "횟수를 확인하지 못했습니다.",
};

export async function fetchDeepStatus(): Promise<DeepQuota> {
  try {
    const res = await fetch(`${AI}/v1/deep`, { cache: "no-store", signal: AbortSignal.timeout(4000) });
    const data = (await res.json()) as Partial<DeepQuota>;
    if (res.ok && typeof data.remaining === "number" && typeof data.used === "number" && data.date) {
      return {
        ok: true,
        limit: data.limit ?? 10,
        used: data.used,
        remaining: data.remaining,
        resets: data.resets || UNKNOWN.resets,
        date: data.date,
      };
    }
  } catch {
    /* 안내 서비스가 없으면 남은 횟수를 10으로 만들지 않는다. */
  }
  return UNKNOWN;
}

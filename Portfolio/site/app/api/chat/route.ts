import { fetchDeepStatus } from "@/lib/deepQuota";

const AI = process.env.PORTFOLIO_AI_URL || "http://127.0.0.1:5055";
const NO_STORE = { "Cache-Control": "no-store" };

export const runtime = "nodejs";
export const maxDuration = 300;

export async function GET() {
  try {
    const res = await fetch(`${AI}/health`, { signal: AbortSignal.timeout(4000) });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      {
        ok: false,
        ready: false,
        detail: "안내 서비스가 꺼져 있습니다. Portfolio/ai 를 먼저 띄우세요.",
      },
      { status: 503 },
    );
  }
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ detail: "JSON이 아닙니다." }, { status: 400 });
  }
  const payload = body as { messages?: unknown; deep?: unknown; model?: unknown };
  const messages = payload.messages;
  const deep = payload.deep === true;
  const model = payload.model === "gemma4:12b" ? "gemma4:12b" : "gemma4:e4b";
  if (!Array.isArray(messages) || messages.length === 0) {
    return Response.json({ detail: "messages가 필요합니다." }, { status: 400 });
  }
  try {
    const res = await fetch(`${AI}/v1/guide`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages, deep, model }),
      signal: AbortSignal.timeout(deep ? 290000 : 160000),
    });
    const data = await res.json();
    const quota = data && typeof data === "object" && data.quota ? data.quota : await fetchDeepStatus();
    const reply = data && typeof data === "object" ? { ...data, quota } : { quota };
    return Response.json(reply, { status: res.status, headers: NO_STORE });
  } catch {
    return Response.json(
      {
        detail: "안내 서비스에 연결하지 못했습니다. Flask가 5055에서 떠 있는지 확인하세요.",
        quota: await fetchDeepStatus(),
      },
      { status: 503, headers: NO_STORE },
    );
  }
}

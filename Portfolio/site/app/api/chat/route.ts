import { finishDeep, refundDeep, reserveDeep } from "@/lib/deepQuota";

const AI = process.env.PORTFOLIO_AI_URL || "http://127.0.0.1:5055";

export const runtime = "nodejs";
export const maxDuration = 600;

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
  const payload = body as { messages?: unknown; deep?: unknown };
  const messages = payload.messages;
  const deep = payload.deep === true;
  if (!Array.isArray(messages) || messages.length === 0) {
    return Response.json({ detail: "messages가 필요합니다." }, { status: 400 });
  }
  let reservation = 0;
  if (deep) {
    const gate = reserveDeep();
    if (!gate.ok) {
      return Response.json(
        { detail: gate.detail, used: gate.used, limit: gate.limit, remaining: gate.remaining },
        { status: 429 },
      );
    }
    reservation = gate.id;
  }
  try {
    const res = await fetch(`${AI}/v1/guide`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages, deep }),
      signal: AbortSignal.timeout(deep ? 600000 : 160000),
    });
    const data = await res.json();
    const answer = typeof data?.answer === "string" ? data.answer : "";
    const failed = answer.startsWith("문서에서는 답을 만들지 못했습니다");
    if (reservation) {
      if (res.ok && !failed) finishDeep(reservation);
      else refundDeep(reservation);
    }
    return Response.json(data, { status: res.status });
  } catch {
    if (reservation) refundDeep(reservation);
    return Response.json(
      { detail: "안내 서비스에 연결하지 못했습니다. Flask가 5055에서 떠 있는지 확인하세요." },
      { status: 503 },
    );
  }
}

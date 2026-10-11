const AI = process.env.PORTFOLIO_AI_URL || "http://127.0.0.1:5055";

export const runtime = "nodejs";
export const maxDuration = 120;

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
  const messages = (body as { messages?: unknown }).messages;
  if (!Array.isArray(messages) || messages.length === 0) {
    return Response.json({ detail: "messages가 필요합니다." }, { status: 400 });
  }
  try {
    const res = await fetch(`${AI}/v1/guide`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages }),
      signal: AbortSignal.timeout(110000),
    });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      { detail: "안내 서비스에 연결하지 못했습니다. Flask가 5055에서 떠 있는지 확인하세요." },
      { status: 503 },
    );
  }
}

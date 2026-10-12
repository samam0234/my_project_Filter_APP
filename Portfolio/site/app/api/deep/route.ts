import { fetchDeepStatus } from "@/lib/deepQuota";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json(await fetchDeepStatus(), { headers: { "Cache-Control": "no-store" } });
}

import { deepStatus } from "@/lib/deepQuota";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export function GET() {
  return Response.json(deepStatus());
}

import { proxyToBackend } from "../../../lib/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  return proxyToBackend(request, "/signup");
}

export async function POST(request: Request): Promise<Response> {
  return proxyToBackend(request, "/signup");
}

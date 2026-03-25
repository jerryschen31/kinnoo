import { NextResponse, type NextRequest } from "next/server";

export function buildSecurityHeaders(nodeEnv: string | undefined): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
  };

  if ((nodeEnv ?? "").toLowerCase() === "production") {
    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
  }

  return headers;
}

export function middleware(_request: NextRequest) {
  const response = NextResponse.next();
  const securityHeaders = buildSecurityHeaders(process.env.NODE_ENV);

  for (const [name, value] of Object.entries(securityHeaders)) {
    response.headers.set(name, value);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

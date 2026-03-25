import { NextResponse, type NextRequest } from "next/server";

export function buildSecurityHeaders(nodeEnv: string | undefined): Record<string, string> {
  const isProduction = (nodeEnv ?? "").toLowerCase() === "production";
  const contentSecurityPolicy = isProduction
    ? [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https: wss:",
        "frame-ancestors 'none'",
      ].join("; ")
    : [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://static.cloudflareinsights.com",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https: http: ws: wss:",
        "frame-ancestors 'none'",
      ].join("; ");

  const headers: Record<string, string> = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": contentSecurityPolicy,
  };

  if (isProduction) {
    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
  }

  return headers;
}

export function proxy(_request: NextRequest) {
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
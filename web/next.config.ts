import type { NextConfig } from "next";

function normalizeBackendUrl(rawUrl: string | undefined): string {
  const trimmed = rawUrl?.trim();
  if (!trimmed) {
    return "http://localhost:8000";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

// BACKEND_URL is the primary contract for phase 5 integration.
// KINNOO_API_BASE_URL is retained as a compatibility fallback.
const backendUrl = normalizeBackendUrl(
  process.env.BACKEND_URL ?? process.env.KINNOO_API_BASE_URL,
);

// Proxy rewrites preserve inbound forwarding headers.
// Backend relies on X-Forwarded-For and X-Request-Id when present.

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/api/login",
        destination: `${backendUrl}/login`,
      },
      {
        source: "/api/logout",
        destination: `${backendUrl}/logout`,
      },
    ];
  },
};

export default nextConfig;

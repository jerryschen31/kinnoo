import type { NextConfig } from "next";

const apiBaseUrl = process.env.KINNOO_API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/bff/login",
        destination: `${apiBaseUrl}/login`,
      },
    ];
  },
};

export default nextConfig;

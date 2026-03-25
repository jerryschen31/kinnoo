import { describe, expect, it } from "vitest";

import { buildSecurityHeaders } from "../middleware";

describe("Security headers middleware", () => {
  it("includes required baseline security headers", () => {
    const headers = buildSecurityHeaders("development");

    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["Content-Security-Policy"]).toBe("default-src 'self'");
  });

  it("sets HSTS only in production", () => {
    const devHeaders = buildSecurityHeaders("development");
    const prodHeaders = buildSecurityHeaders("production");

    expect(devHeaders["Strict-Transport-Security"]).toBeUndefined();
    expect(prodHeaders["Strict-Transport-Security"]).toBe(
      "max-age=31536000; includeSubDomains",
    );
  });
});

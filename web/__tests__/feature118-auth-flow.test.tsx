import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("feature118 redirect auth flow", () => {
  it("keeps login/logout API routes proxying to backend redirect endpoints", () => {
    const loginRoute = readFileSync(resolve(process.cwd(), "app/api/login/route.ts"), "utf-8");
    const logoutRoute = readFileSync(resolve(process.cwd(), "app/api/logout/route.ts"), "utf-8");
    const callbackRoute = readFileSync(resolve(process.cwd(), "app/auth/callback/route.ts"), "utf-8");

    expect(loginRoute).toContain('proxyToBackend(request, "/login")');
    expect(logoutRoute).toContain('proxyToBackend(request, "/logout")');
    expect(callbackRoute).toContain('proxyToBackend(request, "/auth/callback")');
  });

  it("removes custom password-post login UX from login page", () => {
    const loginPage = readFileSync(resolve(process.cwd(), "app/(public)/login/page.tsx"), "utf-8");

    expect(loginPage).toContain("Continue to Login");
    expect(loginPage).not.toContain("type=\"password\"");
    expect(loginPage).not.toContain("validateLoginFields");
  });
});

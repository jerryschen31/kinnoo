import { describe, expect, it, vi } from "vitest";

const { redirectMock, cookiesMock } = vi.hoisted(() => ({
  redirectMock: vi.fn(),
  cookiesMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

vi.mock("next/headers", () => ({
  cookies: cookiesMock,
}));

import AuthLayout from "../app/(auth)/layout";

describe("Auth layout", () => {
  it("redirects to /login when /api/auth/me returns 401", async () => {
    redirectMock.mockReset();
    cookiesMock.mockResolvedValue({ toString: () => "kinnoo_session=bad" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));

    await AuthLayout({ children: <div>content</div> });

    expect(redirectMock).toHaveBeenCalledWith("/login");
  });

  it("renders children when /api/auth/me succeeds", async () => {
    redirectMock.mockReset();
    cookiesMock.mockResolvedValue({ toString: () => "kinnoo_session=good" });
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ user_id: "u1" }), { status: 200 }));

    const view = await AuthLayout({ children: <div>ok</div> });

    expect(redirectMock).not.toHaveBeenCalled();
    expect(view).toBeTruthy();
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/auth/me",
      expect.objectContaining({
        method: "GET",
        cache: "no-store",
      }),
    );
  });
});

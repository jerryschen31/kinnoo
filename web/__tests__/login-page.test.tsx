import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

import LoginPage from "../app/(public)/login/page";

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  vi.restoreAllMocks();
});

describe("Login page", () => {
  it("renders required fields and forgot-password link", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText("Username (E-mail)")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Login" })).toBeTruthy();

    const forgotPasswordLink = screen.getByRole("link", {
      name: "Forgot your password?",
    });
    expect(forgotPasswordLink).toBeTruthy();
    expect(forgotPasswordLink.getAttribute("href")).toBe("/forgot-password");
  });

  it("blocks invalid submissions and renders field validation errors", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 200 }),
    );

    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    expect(screen.getByText("Email is required.")).toBeTruthy();
    expect(screen.getByText("Password is required.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Username (E-mail)"), {
      target: { value: "not-an-email" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "hunter2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    expect(screen.getByText("Enter a valid email address.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("shows loading and disabled state while login request is in-flight", async () => {
    let resolveLoginPost: ((value: Response) => void) | undefined;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      if (typeof input === "string" && input === "/api/login" && (init?.method ?? "GET") === "GET") {
        return Promise.resolve(new Response('<input name="csrf_token" value="token-123" />', { status: 200 }));
      }

      if (typeof input === "string" && input === "/api/login" && init?.method === "POST") {
        return new Promise<Response>((resolve) => {
          resolveLoginPost = resolve;
        });
      }

      return Promise.resolve(new Response(null, { status: 500 }));
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Username (E-mail)"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "super-secret" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    const loadingButton = screen.getByRole("button", { name: "Logging in..." });
    expect(loadingButton).toBeTruthy();
    expect(loadingButton.hasAttribute("disabled")).toBe(true);
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // CSRF GET resolves first, then login POST is issued.
    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    resolveLoginPost?.(new Response(null, { status: 200 }));

    await waitFor(() => {
      const idleButton = screen.getByRole("button", { name: "Login" });
      expect(idleButton.hasAttribute("disabled")).toBe(false);
    });
  });

  it("submits with credentials include and does not persist tokens to browser storage", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      if (typeof input === "string" && input === "/api/login" && (init?.method ?? "GET") === "GET") {
        return Promise.resolve(new Response('<input name="csrf_token" value="token-123" />', { status: 200 }));
      }

      if (typeof input === "string" && input === "/api/login" && init?.method === "POST") {
        return Promise.resolve(new Response(null, { status: 200 }));
      }

      return Promise.resolve(new Response(null, { status: 500 }));
    });
    const storageSetItemSpy = vi.spyOn(Storage.prototype, "setItem");

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Username (E-mail)"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "super-secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    const [requestUrl, requestInit] = fetchSpy.mock.calls[1] ?? [];
    expect(requestUrl).toBe("/api/login");
    expect((requestInit as RequestInit)?.credentials).toBe("include");
    expect(storageSetItemSpy).not.toHaveBeenCalled();
  });

  it("redirects to /registry after successful login", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 200 }));

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Username (E-mail)"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "super-secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/registry");
    });
  });

  it("shows safe inline submit error when backend rejects credentials", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Username (E-mail)"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "bad-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(
        screen.getByText("Unable to sign in. Check your credentials and try again."),
      ).toBeTruthy();
    });
    expect(pushMock).not.toHaveBeenCalled();
  });
});

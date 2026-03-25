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
    let resolveFetch: ((value: Response) => void) | undefined;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
    );

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

    resolveFetch?.(new Response(null, { status: 200 }));

    await waitFor(() => {
      const idleButton = screen.getByRole("button", { name: "Login" });
      expect(idleButton.hasAttribute("disabled")).toBe(false);
    });
  });

  it("submits with credentials include and does not persist tokens to browser storage", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 200 }),
    );
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
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    const [requestUrl, requestInit] = fetchSpy.mock.calls[0] ?? [];
    expect(requestUrl).toBe("/api/bff/login");
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
});

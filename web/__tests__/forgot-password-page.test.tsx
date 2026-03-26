import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordPage from "../app/(public)/forgot-password/page";

describe("ForgotPasswordPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows validation error when email is blank", async () => {
    render(<ForgotPasswordPage />);

    fireEvent.click(screen.getByRole("button", { name: "Send Reset Link" }));

    expect(await screen.findByText("Email is required.")).toBeTruthy();
  });

  it("shows generic confirmation message after successful request", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "person@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Reset Link" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    expect(await screen.findByText("If an account exists with that email, you'll receive a reset link.")).toBeTruthy();
  });
});

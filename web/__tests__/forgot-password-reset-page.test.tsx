import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ResetPasswordPage from "../app/(public)/forgot-password/reset/page";

describe("ResetPasswordPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("validates short password", async () => {
    render(<ResetPasswordPage searchParams={{ token: "abc123" }} />);

    fireEvent.change(screen.getByLabelText("New password"), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText("Confirm new password"), {
      target: { value: "short" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }));

    expect(await screen.findByText("Password must be at least 10 characters.")).toBeTruthy();
  });

  it("shows success state after valid reset", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<ResetPasswordPage searchParams={{ token: "abc123" }} />);

    fireEvent.change(screen.getByLabelText("New password"), {
      target: { value: "long-enough-password" },
    });
    fireEvent.change(screen.getByLabelText("Confirm new password"), {
      target: { value: "long-enough-password" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    expect(await screen.findByText("Password reset complete.")).toBeTruthy();
  });
});

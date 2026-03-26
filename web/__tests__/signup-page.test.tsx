import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import MainLayout from "../components/blocks/MainLayout";
import LoginPage from "../app/(public)/login/page";
import SignupPage from "../app/(public)/signup/page";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  vi.restoreAllMocks();
});

describe("Sign up entry points and signup page", () => {
  it("renders Sign Up CTAs in layout and login page routing to /signup", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    const navSignupLink = screen.getByRole("link", { name: "Sign Up" });
    expect(navSignupLink).toBeTruthy();
    expect(navSignupLink.getAttribute("href")).toBe("/signup");

    cleanup();
    render(<LoginPage />);

    const loginSignupLink = screen.getByRole("link", { name: "Sign Up" });
    expect(loginSignupLink).toBeTruthy();
    expect(loginSignupLink.getAttribute("href")).toBe("/signup");
  });

  it("validates email and shows confirmation state for valid submit", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

    render(<SignupPage />);

    fireEvent.click(screen.getByRole("button", { name: "Send Verification Link" }));
    expect(screen.getByText("Email is required.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "invalid-email" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Verification Link" }));
    expect(screen.getByText("Enter a valid email address.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "dev@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Verification Link" }));

    await waitFor(() => {
      expect(screen.getByText("Check your email for a verification link.")).toBeTruthy();
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});

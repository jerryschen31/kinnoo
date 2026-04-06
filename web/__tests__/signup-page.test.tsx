import { cleanup, render, screen } from "@testing-library/react";
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

  it("renders invite-only message with one Contact Me action", () => {
    render(<SignupPage />);

    expect(
      screen.getByText("Sign up is currently invite-only. Please contact me for early access."),
    ).toBeTruthy();

    const contactLink = screen.getByRole("link", { name: "Contact Me" });
    expect(contactLink).toBeTruthy();
    expect(contactLink.getAttribute("href")).toBe(
      "https://twitter.com/messages/compose?recipient_id=4118511499",
    );
    expect(contactLink.getAttribute("target")).toBe("_blank");

    expect(screen.getAllByRole("link", { name: "Contact Me" })).toHaveLength(1);
  });

  it("does not render legacy signup form elements", () => {
    render(<SignupPage />);

    expect(screen.queryByLabelText("Email address")).toBeNull();
    expect(screen.queryByRole("button", { name: "Send Verification Link" })).toBeNull();
    expect(screen.queryByText("Check your email for a verification link.")).toBeNull();
  });
});

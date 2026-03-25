import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LoginPage from "../app/(public)/login/page";

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
});

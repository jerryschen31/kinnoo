import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import MainLayout from "../components/blocks/MainLayout";

afterEach(() => {
  cleanup();
});

describe("MainLayout", () => {
  it("renders hamburger menu and auth buttons", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    expect(screen.getByRole("button", { name: /open menu/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Login" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Sign Up" })).toBeTruthy();
  });

  it("opens menu sheet with expected navigation links", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    expect(screen.getByRole("link", { name: "GitHub" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Docs" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Report an Issue" })).toBeTruthy();
  });

  it("includes responsive classes for mobile-safe header behavior", () => {
    const { container } = render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    const headerRow = container.querySelector("header > div");
    expect(headerRow?.className).toContain("gap-2");
    expect(headerRow?.className).toContain("sm:px-4");

    const authButtons = screen.getAllByRole("link", { name: /login|sign up/i });
    for (const button of authButtons) {
      expect(button.className).toContain("max-[399px]:text-xs");
      expect(button.className).toContain("max-[399px]:px-2");
    }

    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));
    const dialog = container.ownerDocument.querySelector("[role='dialog']");
    expect(dialog?.className).toContain("w-full");
    expect(dialog?.className).toContain("sm:w-80");
  });
});

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
});

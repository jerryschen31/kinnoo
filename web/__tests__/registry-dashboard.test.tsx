import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import RegistryPage from "../app/(auth)/registry/page";

afterEach(() => {
  cleanup();
});

describe("Registry dashboard", () => {
  it("renders secondary nav controls", () => {
    render(<RegistryPage />);

    expect(screen.getByRole("button", { name: "My Agents" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Search" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Logout" })).toBeTruthy();
  });

  it("defaults to My Agents view on initial render", () => {
    render(<RegistryPage />);

    const myAgentsButton = screen.getByRole("button", { name: "My Agents" });
    expect(myAgentsButton.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("heading", { name: "My Agents" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    expect(screen.getByRole("heading", { name: "Search" })).toBeTruthy();
  });
});

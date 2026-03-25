import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

  it("renders search query input and show-only-my-agents checkbox", async () => {
    render(<RegistryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => {
      expect(screen.getByTestId("registry-search-view")).toBeTruthy();
    });

    const queryInput = screen.getByLabelText("Search public agents") as HTMLInputElement;
    const onlyMineCheckbox = screen.getByRole("checkbox", { name: "Show only my agents" });

    fireEvent.change(queryInput, { target: { value: "langgraph" } });
    fireEvent.click(onlyMineCheckbox);

    expect(queryInput.value).toBe("langgraph");
    expect((onlyMineCheckbox as HTMLInputElement).checked).toBe(true);
  });

  it("switches between tabs with stable state and view content", async () => {
    render(<RegistryPage />);

    expect(screen.getByTestId("registry-my-agents-view")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect(screen.getByTestId("registry-search-view")).toBeTruthy();
    });

    const queryInput = screen.getByLabelText("Search public agents") as HTMLInputElement;
    fireEvent.change(queryInput, { target: { value: "pydantic" } });

    fireEvent.click(screen.getByRole("button", { name: "My Agents" }));
    await waitFor(() => {
      expect(screen.getByTestId("registry-my-agents-view")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect((screen.getByLabelText("Search public agents") as HTMLInputElement).value).toBe(
        "pydantic",
      );
    });
  });
});

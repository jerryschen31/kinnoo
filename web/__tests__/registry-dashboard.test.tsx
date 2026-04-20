import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import RegistryPage from "../app/(auth)/registry/page";

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Registry dashboard", () => {
  it("renders secondary nav controls", () => {
    render(<RegistryPage />);

    expect(screen.getByRole("button", { name: "My Agents" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Search" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Logout" })).toBeTruthy();
  });

  it("defaults to My Agents view on initial render", async () => {
    render(<RegistryPage />);

    const myAgentsButton = screen.getByRole("button", { name: "My Agents" });
    expect(myAgentsButton.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("heading", { name: "My Agents" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Search" })).toBeTruthy();
    });
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

  it("uses /api proxy routes and handles loading, empty, and query-driven error states", async () => {
    let resolveAgentsFetch: ((value: Response) => void) | undefined;
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);

      if (url === "/api/agents?show_only_mine=true") {
        return new Promise<Response>((resolve) => {
          resolveAgentsFetch = resolve;
        });
      }

      if (url.startsWith("/api/search")) {
        return Promise.reject(new Error("search service unavailable"));
      }

      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    expect(screen.getByText("Loading agents...")).toBeTruthy();

    resolveAgentsFetch?.(jsonResponse([]));

    await waitFor(() => {
      expect(screen.getByText("No agents published yet.")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => {
      expect(screen.getByTestId("registry-search-view")).toBeTruthy();
    });

    expect(screen.queryByText("Unable to search agents right now.")).toBeNull();

    fireEvent.change(screen.getByLabelText("Search public agents"), {
      target: { value: "langgraph" },
    });

    await waitFor(() => {
      expect(screen.getByText("Unable to search agents right now.")).toBeTruthy();
    });

    const calledUrls = fetchSpy.mock.calls.map(([url]) => String(url));
    expect(calledUrls.some((url) => url === "/api/agents?show_only_mine=true")).toBe(true);
    expect(calledUrls.some((url) => url.startsWith("/api/search"))).toBe(true);
  });

  it("submits logout as navigation-style POST with csrf token", () => {
    document.cookie = "kinnoo_csrf=test-csrf-token";
    const submitSpy = vi
      .spyOn(HTMLFormElement.prototype, "submit")
      .mockImplementation(() => undefined);

    render(<RegistryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(submitSpy).toHaveBeenCalledTimes(1);
    const logoutForm = document.querySelector(
      'form[action="/api/logout"][method="POST"]',
    ) as HTMLFormElement | null;
    expect(logoutForm).toBeTruthy();
    const csrfInput = logoutForm?.querySelector(
      'input[name="csrf_token"]',
    ) as HTMLInputElement | null;
    expect(csrfInput?.value).toBe("test-csrf-token");
  });
});

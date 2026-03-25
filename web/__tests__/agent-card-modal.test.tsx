import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AgentCard from "../components/blocks/AgentCard";
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
});

describe("AgentCard", () => {
  it("renders required metadata fields and clickable name", () => {
    const onNameClick = vi.fn();

    render(
      <AgentCard
        agent={{
          tenant_slug: "acme",
          agent_slug: "calendar-helper",
          version: "1.2.3",
          author: "jerry",
          framework: "langgraph",
          size: 4096,
          description: "Helps with calendar workflows.",
        }}
        onNameClick={onNameClick}
      />, 
    );

    expect(screen.getByText("Tenant")).toBeTruthy();
    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByText("Version")).toBeTruthy();
    expect(screen.getByText("Author")).toBeTruthy();
    expect(screen.getByText("Framework")).toBeTruthy();
    expect(screen.getByText("Size")).toBeTruthy();
    expect(screen.getByText("Description")).toBeTruthy();

    const nameButton = screen.getByRole("button", { name: "calendar-helper" });
    fireEvent.click(nameButton);

    expect(onNameClick).toHaveBeenCalledTimes(1);
  });

  it("opens manifest modal from name click and closes using X", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/agents") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }
      if (url === "/api/agents/acme/calendar-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            manifest: { name: "calendar-helper" },
          }),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    const agentNameButton = await screen.findByRole("button", { name: "calendar-helper" });
    fireEvent.click(agentNameButton);

    expect(await screen.findByRole("heading", { name: "Agent Manifest" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Close manifest modal" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Agent Manifest" })).toBeNull();
    });
  });

  it("fetches detail endpoint and renders manifest payload", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/agents") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }
      if (url === "/api/agents/acme/calendar-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            versions: [{ version: "1.2.3" }],
            manifest: { framework: "langgraph" },
          }),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    fireEvent.click(await screen.findByRole("button", { name: "calendar-helper" }));

    await waitFor(() => {
      expect(screen.getByText(/"framework": "langgraph"/)).toBeTruthy();
    });

    const urls = fetchSpy.mock.calls.map(([url]) => String(url));
    expect(urls).toContain("/api/agents/acme/calendar-helper");
  });

  it("shows deterministic install command in search modal and copy feedback", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);

      if (url === "/api/agents") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }

      if (url.startsWith("/api/search")) {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "public-helper",
              version: "2.0.0",
              description: "public",
            },
          ]),
        );
      }

      if (url === "/api/agents/acme/public-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "public-helper",
            manifest: { name: "public-helper" },
          }),
        );
      }

      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(await screen.findByRole("button", { name: "public-helper" }));

    await waitFor(() => {
      expect(screen.getByText("kinnoo install acme/public-helper@2.0.0")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("kinnoo install acme/public-helper@2.0.0");
      expect(screen.getByRole("button", { name: "Copied!" })).toBeTruthy();
    });
  });
});

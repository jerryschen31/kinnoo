import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LandingPage from "../app/(public)/page";

afterEach(() => {
  cleanup();
});

describe("Landing page", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it("renders exact hero title and sub-headline", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "kinnoo",
      }),
    ).toBeTruthy();

    expect(screen.getByText("Building AI agents together")).toBeTruthy();

    expect(
      screen.getByText(
        "The open, secure platform to package, publish and share any AI agent",
      ),
    ).toBeTruthy();

    expect(
      screen.getByText(
        "Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, an OpenClaw daemon — and give it a portable, version-controlled, signed package that anyone can install and run",
      ),
    ).toBeTruthy();
  });

  it("renders terminal command and supports copy feedback", async () => {
    render(<LandingPage />);

    expect(screen.getByText("pip install kinnoo")).toBeTruthy();
    const copyButton = screen.getByRole("button", { name: "Copy install command" });
    expect(copyButton).toBeTruthy();

    fireEvent.click(copyButton);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("pip install kinnoo");
    expect(await screen.findByText("Copied!")).toBeTruthy();
  });

  it("renders all six feature cards with exact copy", () => {
    render(<LandingPage />);

    const expectedCards: Array<{ title: string; description: string }> = [
      {
        title: "Supports common AI agent frameworks",
        description:
          "Initialize, import or install AI agents developed with LangChain, LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw and more.",
      },
      {
        title: "One-command packaging",
        description:
          "Bundle your agent, its dependencies, assets, and state into a single portable .kno archive — ready to share or publish.",
      },
      {
        title: "Discover and install from a registry",
        description:
          "Publish agents to a hosted registry where others can search, inspect, and install them with kinnoo install — like npm, but for agents.",
      },
      {
        title: "Built to run real-world agents",
        description:
          "kinnoo handles environment setup, dependency isolation, and runtime wiring for Python and Node.js agents, including one-shot and long-running daemon-based agents.",
      },
      {
        title: "Security built-in",
        description:
          "Signed archives, permission declarations, static security sweeps, dependency audits, preflight checks, runtime monitoring, and a kill switch — trust what you run.",
      },
      {
        title: "Inspect before you run",
        description:
          "Review any agent's manifest, dependencies, environment variables, permissions, and services before installation — no surprises.",
      },
    ];

    for (const card of expectedCards) {
      expect(screen.getByRole("heading", { level: 3, name: card.title })).toBeTruthy();
      expect(screen.getByText(card.description)).toBeTruthy();
    }
  });

  it("exposes hover/focus hooks and avoids horizontal overflow classes", () => {
    const { container } = render(<LandingPage />);

    const grid = screen.getByTestId("feature-grid");
    expect(grid.className).toContain("grid-cols-1");
    expect(grid.className).toContain("sm:grid-cols-2");

    const cards = container.querySelectorAll("article");
    expect(cards.length).toBe(6);

    cards.forEach((card) => {
      expect(card.className).toContain("hover:border-kinnoo-accent/60");
      expect(card.className).toContain("focus-within:ring-1");
      expect(card.className).toContain("overflow-hidden");
    });
  });

  it("covers hero, terminal preview, and features in one render pass", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "kinnoo",
      }),
    ).toBeTruthy();
    expect(screen.getByText("Building AI agents together")).toBeTruthy();
    expect(screen.getByText("pip install kinnoo")).toBeTruthy();
    expect(screen.getByTestId("feature-grid")).toBeTruthy();
  });
});

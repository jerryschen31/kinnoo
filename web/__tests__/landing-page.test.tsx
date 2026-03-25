import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LandingPage from "../app/(public)/page";

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
        name: "Package, publish, share your AI agents with the world",
      }),
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
});

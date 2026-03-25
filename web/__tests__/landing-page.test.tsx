import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LandingPage from "../app/(public)/page";

describe("Landing page", () => {
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
});

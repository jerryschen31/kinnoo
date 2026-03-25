import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import AgentCard from "../components/blocks/AgentCard";

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
});

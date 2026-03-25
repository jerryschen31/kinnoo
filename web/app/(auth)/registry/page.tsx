"use client";

import { useState } from "react";

import RegistryNav from "../../../components/blocks/RegistryNav";

export default function RegistryPage() {
  const [activeView, setActiveView] = useState<"my-agents" | "search">("my-agents");

  return (
    <div className="space-y-6">
      <RegistryNav activeView={activeView} onSelectView={setActiveView} />

      <section
        aria-live="polite"
        className="rounded-card border border-white/15 bg-[#222222] p-5"
        data-testid="registry-active-view"
      >
        {activeView === "my-agents" ? (
          <div>
            <h1 className="text-2xl font-semibold text-kinnoo-text">My Agents</h1>
            <p className="mt-2 text-sm text-white/70">Your published agents will appear here.</p>
          </div>
        ) : (
          <div>
            <h1 className="text-2xl font-semibold text-kinnoo-text">Search</h1>
            <p className="mt-2 text-sm text-white/70">
              Search controls and public agent results will appear here.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

"use client";

import { AnimatePresence, motion } from "framer-motion";

type RegistryView = "my-agents" | "search";

type RegistryTabsProps = {
  activeView: RegistryView;
  searchQuery: string;
  showOnlyMyAgents: boolean;
  onSearchQueryChange: (value: string) => void;
  onShowOnlyMyAgentsChange: (checked: boolean) => void;
};

const panelMotion = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.16, ease: "easeOut" },
};

export default function RegistryTabs({
  activeView,
  searchQuery,
  showOnlyMyAgents,
  onSearchQueryChange,
  onShowOnlyMyAgentsChange,
}: RegistryTabsProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      {activeView === "my-agents" ? (
        <motion.section
          key="my-agents"
          {...panelMotion}
          aria-live="polite"
          className="rounded-card border border-white/15 bg-[#222222] p-5"
          data-testid="registry-my-agents-view"
        >
          <h1 className="text-2xl font-semibold text-kinnoo-text">My Agents</h1>
          <p className="mt-2 text-sm text-white/70">Your published agents will appear here.</p>
        </motion.section>
      ) : (
        <motion.section
          key="search"
          {...panelMotion}
          aria-live="polite"
          className="space-y-4 rounded-card border border-white/15 bg-[#222222] p-5"
          data-testid="registry-search-view"
        >
          <h1 className="text-2xl font-semibold text-kinnoo-text">Search</h1>
          <div className="space-y-3">
            <label htmlFor="registry-search-query" className="block text-sm font-medium text-white/85">
              Search public agents
            </label>
            <input
              id="registry-search-query"
              name="searchQuery"
              type="text"
              value={searchQuery}
              onChange={(event) => onSearchQueryChange(event.target.value)}
              placeholder="Search by tenant, name, framework..."
              className="w-full rounded-button border border-white/20 bg-black/35 px-3 py-2 text-sm text-kinnoo-text placeholder:text-white/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
            />
            <label className="inline-flex items-center gap-2 text-sm text-white/80">
              <input
                type="checkbox"
                checked={showOnlyMyAgents}
                onChange={(event) => onShowOnlyMyAgentsChange(event.target.checked)}
                className="h-4 w-4 rounded border-white/30 bg-black/35 text-kinnoo-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
              />
              Show only my agents
            </label>
          </div>
        </motion.section>
      )}
    </AnimatePresence>
  );
}

"use client";

import { useState } from "react";

import RegistryNav from "../../../components/blocks/RegistryNav";
import RegistryTabs from "../../../components/blocks/RegistryTabs";

export default function RegistryPage() {
  const [activeView, setActiveView] = useState<"my-agents" | "search">("my-agents");
  const [searchQuery, setSearchQuery] = useState("");
  const [showOnlyMyAgents, setShowOnlyMyAgents] = useState(false);

  return (
    <div className="space-y-6">
      <RegistryNav activeView={activeView} onSelectView={setActiveView} />
      <RegistryTabs
        activeView={activeView}
        searchQuery={searchQuery}
        showOnlyMyAgents={showOnlyMyAgents}
        onSearchQueryChange={setSearchQuery}
        onShowOnlyMyAgentsChange={setShowOnlyMyAgents}
      />
    </div>
  );
}

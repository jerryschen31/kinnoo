"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { buildInstallCommand } from "../../lib/install-command";
import { fetchAgentDetail, type AgentDetail, type AgentSummary } from "../../lib/registry-client";

type AgentManifestModalProps = {
  selectedAgent: AgentSummary | null;
  selectedSource: "my-agents" | "search" | null;
  onClose: () => void;
};

export default function AgentManifestModal({
  selectedAgent,
  selectedSource,
  onClose,
}: AgentManifestModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeManifestTab, setActiveManifestTab] = useState<"registry" | "agent">("registry");

  useEffect(() => {
    if (!selectedAgent) {
      setIsLoading(false);
      setError(null);
      setDetail(null);
      setCopied(false);
      setActiveManifestTab("registry");
      return;
    }

    let cancelled = false;

    const loadDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const nextDetail = await fetchAgentDetail(selectedAgent.tenant_slug, selectedAgent.agent_slug);
        if (!cancelled) {
          setDetail(nextDetail);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load agent manifest details right now.");
          setDetail(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadDetail();

    return () => {
      cancelled = true;
    };
  }, [selectedAgent]);

  const prettyRegistryManifest = useMemo(() => {
    if (!detail) {
      return "";
    }

    // Keep Registry Manifest focused on registry metadata only.
    const { agent_manifest: _agentManifest, manifest: _manifest, ...registryManifestOnly } = detail;
    return JSON.stringify(registryManifestOnly, null, 2);
  }, [detail]);

  const resolvedAgentManifest = useMemo(() => {
    if (!detail || typeof detail !== "object") {
      return null;
    }

    if (
      "agent_manifest" in detail &&
      detail.agent_manifest &&
      typeof detail.agent_manifest === "object" &&
      !Array.isArray(detail.agent_manifest)
    ) {
      return detail.agent_manifest;
    }

    if (
      "manifest" in detail &&
      detail.manifest &&
      typeof detail.manifest === "object" &&
      !Array.isArray(detail.manifest)
    ) {
      return detail.manifest;
    }

    return null;
  }, [detail]);

  const prettyAgentManifest = useMemo(() => {
    if (!resolvedAgentManifest) {
      return "";
    }
    return JSON.stringify(resolvedAgentManifest, null, 2);
  }, [resolvedAgentManifest]);

  const installCommand = useMemo(() => {
    if (!selectedAgent) {
      return null;
    }
    return buildInstallCommand(selectedAgent);
  }, [selectedAgent]);

  const handleCopyInstallCommand = async () => {
    if (!installCommand) {
      return;
    }

    await navigator.clipboard.writeText(installCommand);
    setCopied(true);
    window.setTimeout(() => {
      setCopied(false);
    }, 1200);
  };

  return (
    <Dialog.Root open={Boolean(selectedAgent)} onOpenChange={(open) => (!open ? onClose() : undefined)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(52rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-card border border-white/15 bg-[#222222] p-5 shadow-xl">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <Dialog.Title className="text-lg font-semibold text-kinnoo-text">Agent Manifest</Dialog.Title>
              <Dialog.Description className="text-sm text-white/70">
                {selectedAgent
                  ? `${selectedAgent.tenant_slug}/${selectedAgent.agent_slug}`
                  : "No agent selected"}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close manifest modal"
                onClick={onClose}
                className="inline-flex h-8 w-8 items-center justify-center rounded-button border border-white/20 text-white/80 transition hover:border-kinnoo-accent hover:text-kinnoo-accent"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          {isLoading ? <p className="text-sm text-white/70">Loading manifest details...</p> : null}
          {error ? (
            <p role="alert" className="text-sm text-red-300">
              {error}
            </p>
          ) : null}
          {!isLoading && !error && detail ? (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("registry")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "registry"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Registry Manifest
                </button>
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("agent")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "agent"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Agent Manifest
                </button>
              </div>

              {activeManifestTab === "registry" ? (
                <pre className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                  {prettyRegistryManifest}
                </pre>
              ) : resolvedAgentManifest ? (
                <pre className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                  {prettyAgentManifest}
                </pre>
              ) : (
                <div className="rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/70">
                  Agent manifest (kinnoo.yaml) is not available for this record.
                </div>
              )}
            </div>
          ) : null}

          {installCommand ? (
            <div className="mt-4 rounded-card border-2 border-white/25 bg-[#222222] p-4 transition hover:border-[#FF7F00] card-border-1">
              <p className="mb-2 text-xs uppercase tracking-[0.18em] text-white/50">Terminal</p>
              <div className="flex items-center justify-between gap-3">
                <code className="text-sm text-kinnoo-text sm:text-base">{installCommand}</code>
                <button
                  type="button"
                  onClick={handleCopyInstallCommand}
                  className="rounded-button border border-white/20 px-3 py-1 text-sm font-medium text-kinnoo-text transition hover:border-kinnoo-accent hover:text-kinnoo-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

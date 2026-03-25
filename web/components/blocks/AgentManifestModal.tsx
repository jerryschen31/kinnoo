"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { fetchAgentDetail, type AgentDetail, type AgentSummary } from "../../lib/registry-client";

type AgentManifestModalProps = {
  selectedAgent: AgentSummary | null;
  onClose: () => void;
};

export default function AgentManifestModal({ selectedAgent, onClose }: AgentManifestModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentDetail | null>(null);

  useEffect(() => {
    if (!selectedAgent) {
      setIsLoading(false);
      setError(null);
      setDetail(null);
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

  const prettyDetail = useMemo(() => {
    if (!detail) {
      return "";
    }
    return JSON.stringify(detail, null, 2);
  }, [detail]);

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
            <pre className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
              {prettyDetail}
            </pre>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

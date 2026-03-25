export type AgentSummary = {
  tenant_slug: string;
  agent_slug: string;
  version: string;
  author?: string;
  framework?: string;
  size?: number;
  description?: string;
};

export type AgentDetail = {
  tenant_slug: string;
  agent_slug: string;
  versions?: unknown;
  metadata?: unknown;
  manifest?: unknown;
  [key: string]: unknown;
};

type SearchAgentsParams = {
  query: string;
  showOnlyMine: boolean;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchMyAgents(): Promise<AgentSummary[]> {
  return getJson<AgentSummary[]>("/api/agents");
}

export async function searchAgents(params: SearchAgentsParams): Promise<AgentSummary[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.query);
  if (params.showOnlyMine) {
    searchParams.set("show_only_mine", "true");
  }

  const queryString = searchParams.toString();
  const url = queryString.length > 0 ? `/api/search?${queryString}` : "/api/search";

  return getJson<AgentSummary[]>(url);
}

export async function fetchAgentDetail(
  tenantSlug: string,
  agentSlug: string,
): Promise<AgentDetail> {
  return getJson<AgentDetail>(`/api/agents/${tenantSlug}/${agentSlug}`);
}

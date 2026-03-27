type FeatureCard = {
  title: string;
  description: string;
};

const FEATURES: readonly FeatureCard[] = [
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
] as const;

export default function FeatureGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3" data-testid="feature-grid">
      {FEATURES.map((feature) => (
        <article
          key={feature.title}
          className="group min-h-40 overflow-hidden rounded-card border-2 border-white/25 bg-[#222222] p-5 transition hover:-translate-y-0.5 hover:border-[#3B82F6] focus-within:border-[#3B82F6] focus-within:ring-1 focus-within:ring-[#3B82F6]"
        >
          <h3 className="mb-3 text-xl font-semibold leading-snug text-[#F9FAFB]">{feature.title}</h3>
          <p className="text-sm leading-relaxed text-[#F9FAFB] sm:text-base">{feature.description}</p>
        </article>
      ))}
    </div>
  );
}

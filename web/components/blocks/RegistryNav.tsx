type RegistryView = "my-agents" | "search";

type RegistryNavProps = {
  activeView: RegistryView;
  onSelectView: (view: RegistryView) => void;
};

const baseTabClass =
  "rounded-button border px-4 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent";

export default function RegistryNav({ activeView, onSelectView }: RegistryNavProps) {
  return (
    <nav
      aria-label="Registry navigation"
      className="flex flex-wrap items-center gap-2 rounded-card border border-white/15 bg-[#222222] p-3"
    >
      <button
        type="button"
        onClick={() => onSelectView("my-agents")}
        aria-pressed={activeView === "my-agents"}
        className={`${baseTabClass} ${
          activeView === "my-agents"
            ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-text"
            : "border-white/20 text-white/80 hover:border-kinnoo-accent"
        }`}
      >
        My Agents
      </button>
      <button
        type="button"
        onClick={() => onSelectView("search")}
        aria-pressed={activeView === "search"}
        className={`${baseTabClass} ${
          activeView === "search"
            ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-text"
            : "border-white/20 text-white/80 hover:border-kinnoo-accent"
        }`}
      >
        Search
      </button>
      <a
        href="/logout"
        className="ml-auto inline-flex items-center rounded-button border border-white/20 px-4 py-2 text-sm font-medium text-white/80 transition hover:border-kinnoo-accent hover:text-kinnoo-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
      >
        Logout
      </a>
    </nav>
  );
}

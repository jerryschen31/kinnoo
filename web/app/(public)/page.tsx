import TerminalPreview from "../../components/blocks/TerminalPreview";
import FeatureGrid from "../../components/blocks/FeatureGrid";

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-12 pb-12 sm:gap-16 sm:pb-16">
      <section aria-labelledby="landing-hero-title" className="pt-4 sm:pt-8">
        <div className="max-w-4xl space-y-4">
          <h1
            id="landing-hero-title"
            className="text-5xl font-semibold leading-none tracking-tight text-[#3B82F6] sm:text-6xl"
          >
            kinnoo
          </h1>
          <p className="text-2xl font-bold text-[#F9FAFB] sm:text-3xl">
            The package manager for AI agents
          </p>
          <p className="max-w-3xl text-lg leading-relaxed text-white/80 sm:text-xl">
            The open, secure platform to package, publish, test, and operate AI agents across one-shot and daemon-compatible runtimes
          </p>
        </div>
      </section>

      <section aria-label="Terminal preview">
        <div className="max-w-2xl">
          <TerminalPreview />
        </div>
      </section>

      <section aria-label="Features">
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-[#F9FAFB] sm:text-xl">
            Why developers choose Kinnoo
          </h2>
          <p className="text-base leading-relaxed normal-case text-white/80 sm:text-lg">
            Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, or an OpenClaw skill mirrored from ClawHub — and turn it into a signed, versioned, portable package with provenance you can verify before install
          </p>
          <FeatureGrid />
        </div>
      </section>
    </div>
  );
}

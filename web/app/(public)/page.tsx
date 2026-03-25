import TerminalPreview from "../../components/blocks/TerminalPreview";
import FeatureGrid from "../../components/blocks/FeatureGrid";

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-12 pb-12 sm:gap-16 sm:pb-16">
      <section aria-labelledby="landing-hero-title" className="pt-4 sm:pt-8">
        <div className="max-w-4xl space-y-6">
          <h1
            id="landing-hero-title"
            className="text-5xl font-semibold leading-none tracking-tight text-[#3B82F6] sm:text-6xl"
          >
            kinnoo
          </h1>
          <p className="text-base font-semibold uppercase tracking-[0.24em] text-white/75 sm:text-lg">
            Package, publish, share your AI agents with the world
          </p>
          <p className="max-w-3xl text-base leading-relaxed text-white/80 sm:text-lg">
            Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, an OpenClaw daemon — and give it a portable, version-controlled, signed package that anyone can install and run
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
          <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/80 sm:text-base">
            Why builders choose kinnoo
          </h2>
          <FeatureGrid />
        </div>
      </section>
    </div>
  );
}

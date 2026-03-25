import TerminalPreview from "../../components/blocks/TerminalPreview";
import FeatureGrid from "../../components/blocks/FeatureGrid";

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-12 pb-12 sm:gap-16 sm:pb-16">
      <section aria-labelledby="landing-hero-title" className="pt-4 sm:pt-8">
        <div className="max-w-4xl space-y-6">
          <h1
            id="landing-hero-title"
            className="text-4xl font-semibold leading-tight tracking-tight text-kinnoo-text sm:text-5xl"
          >
            Package, publish, share your AI agents with the world
          </h1>
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
          <h2 className="text-2xl font-semibold tracking-tight text-kinnoo-text sm:text-3xl">
            Why builders choose kinnoo
          </h2>
          <FeatureGrid />
        </div>
      </section>
    </div>
  );
}

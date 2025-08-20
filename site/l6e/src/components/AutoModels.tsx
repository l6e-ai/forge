import React from "react";
import Section from "./Section";
import CodeBlock from "./CodeBlock";

const steps = `# Auto Models (alpha)
$ forge models doctor
$ forge models bootstrap --agent agents/my-agent --provider ollama
$ forge up --agents my-agent   # auto-bootstraps if needed`;

export default function AutoModels() {
  return (
    <Section id="auto-models" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-4">Auto Models</h2>
      <p className="text-white/70 max-w-3xl mb-8">
        Ship once; run anywhere. Forge detects the system and installs an optimized open-source model automatically—so
        developers aren&apos;t forced to handpick models and their users don&apos;t sweat the details. Apple Silicon optimized; <i>currently in alpha with Ollama support.</i>
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <h3 className="text-base font-semibold mb-1">For developers</h3>
            <p className="text-white/70 text-sm">
              Build independently of hardware and model constraints. Package your agent, and let Auto Models select the best fit
              at install or run time.
            </p>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <h3 className="text-base font-semibold mb-1">For users</h3>
            <p className="text-white/70 text-sm">
              Run the agent; Forge detects your system and pulls the right models automatically—no setup.
            </p>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <h3 className="text-base font-semibold mb-1">Current support</h3>
            <p className="text-white/70 text-sm">Alpha, Apple Silicon optimized, Ollama-only. More providers coming soon.</p>
          </div>
        </div>
        <div>
          <CodeBlock code={steps} mode="bash" highlight language="bash" themeName="dracula" />
          <div className="text-xs text-white/50 mt-3">Commands and UX may evolve during alpha.</div>
        </div>
      </div>
    </Section>
  );
}



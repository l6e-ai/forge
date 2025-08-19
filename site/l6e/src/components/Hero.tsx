import React from "react";
import Section from "./Section";
import Button from "./Button";
import CodeBlock from "./CodeBlock";

const terminalText = [
  "$ pip install l6e-forge",
  "$ l6e create assistant --template=personal",
  "$ l6e package assistant",
  "📦 Packaged assistant.l6e (ready to deploy)",
  "$ l6e deploy assistant.l6e --target=production",
  "🚀 Agent deployed locally",
  "✨ Your AI runs where you need it.",
].join("\n");

export default function Hero() {
  return (
    <Section className="pt-16 pb-12 sm:pt-24 sm:pb-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs text-white/70 mb-4">
            <span className="h-2 w-2 rounded-full bg-[#00ff88]" /> Open Source • Local-first
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            l6e AI
            <br />
            <span className="text-white/90">Localizing AI for everyone</span>
          </h1>
          <p className="mt-4 text-lg text-white/70 max-w-xl">
            Create portable AI agents that run anywhere. Build once, deploy everywhere. No cloud required.
          </p>
          <div className="mt-6 flex items-center gap-3">
            <Button href="https://github.com/l6e-ai/agent-forge" variant="primary">Create Your First Agent</Button>
            <Button href="https://github.com/l6e-ai/agent-forge" variant="outline">View on GitHub</Button>
          </div>
        </div>
        <div>
          <CodeBlock code={terminalText} mode="bash" />
        </div>
      </div>
    </Section>
  );
}



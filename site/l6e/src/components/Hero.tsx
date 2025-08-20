import React from "react";
import Section from "./Section";
import Button from "./Button";
import CodeBlock from "./CodeBlock";

const terminalText = [
  "$ pip install l6e-forge",
  "$ forge create agent assistant --template=assistant",
  "$ forge pkg build agents/assistant -o dist",
  "📦 Packaged dist/assistant-0.1.0.l6e (ready to ship)",
  "$ forge pkg install dist/assistant-0.1.0.l6e -w /workspaces/prod",
  "$ forge up",
  "🚀 Agent running on your stack",
  "✨ Your AI runs where you need it.",
].join("\n");

export default function Hero() {
  return (
    <Section className="pt-16 pb-12 sm:pt-24 sm:pb-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div>
          <div className="flex flex-col gap-2 mb-4">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs text-white/70">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" /> Open Source • Local-first
            </div>
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-3 py-1 text-[10px] text-[var(--accent)]">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" /> Auto Models (alpha)
            </div>
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs text-white/70">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" /> Your stack, your data
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            l6e AI
            <br />
            <span className="text-white/90">Localize AI for everyone</span>
          </h1>
          <p className="mt-4 text-lg text-white/70 max-w-xl">
            <span className="text-green-500 mb-4">Introducing Forge by l6e, now in alpha:</span>
            <br />
            Create portable AI agents that run anywhere. Plug into local LLM runners like LM Studio and Ollama. Keep your data on your infrastructure—laptops or your VPC—with zero required cloud. Optimized for personal-scale, single-user assistants that run great on Apple Silicon. 
            <br /><br />
            Our Auto Model selector can choose and install optimized OSS model(s) for any system your agent runs on. Out-of-the-box Docker stack included to run small-scale agents on local hardware with minimal configuration.
          </p>
          <div className="mt-6 flex items-center gap-3">
            <Button href="https://github.com/l6e-ai/forge" variant="primary">Create Your First Agent</Button>
            <Button href="https://github.com/l6e-ai/forge" variant="outline">View on GitHub</Button>
          </div>
        </div>
        <div>
          <CodeBlock code={terminalText} mode="bash" highlight language="bash" themeName="dracula" />
        </div>
      </div>
    </Section>
  );
}



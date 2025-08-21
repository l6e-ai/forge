import React from "react";
import Section from "./Section";
import CodeBlock from "./CodeBlock";

const railsSnippet = [
  "# Agents on Rails",
  "$ pip install l6e-forge",
  "$ forge create agent my-agent --template=assistant",
  "$ forge up",
  "",
  "# Local stack: API (8000), Monitor (8321), Chat UI",
  "# Single-user by default (not horizontally scalable)",
  "# Scale later: deploy Qdrant/Postgres and switch adapters",
  "# Adapters-first: swap providers without rewrites",
].join("\n");

export default function AgentsOnRails() {
  return (
    <Section id="agents-on-rails" className="py-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        <div>
          <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-3">Agents on Rails</h2>
          <p className="text-white/70 mb-6 max-w-2xl">
            Rails for agents: opinionated defaults to ship MVPs fast. Bring up a full local stack via
            Docker—API, monitor, chat UI, and pluggable stores (Qdrant/LanceDB, Postgres)—no cloud
            required. Base stack is single-user; scale by deploying backing services and swapping
            adapters. Unlike classic Rails, Forge is adapters-first and ecosystem-friendly: conventions
            speed you up, interfaces keep you from lock-in.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-base font-semibold mb-1">Full local stack</h3>
              <p className="text-white/70 text-sm">Run API, monitor, and chat UI with one command.</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-base font-semibold mb-1">Portable packages</h3>
              <p className="text-white/70 text-sm">Ship a single .l6e file and run it anywhere.</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-base font-semibold mb-1">BYO stores</h3>
              <p className="text-white/70 text-sm">Use Qdrant/LanceDB for vectors and Postgres for state.</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <h3 className="text-base font-semibold mb-1">Opinions without lock-in</h3>
              <p className="text-white/70 text-sm">Adapters-first: pick runners, memory, and DBs; swap providers as you grow.</p>
            </div>
          </div>
        </div>
        <div>
          <CodeBlock
            code={railsSnippet}
            mode="bash"
            highlight
            language="bash"
            themeName="dracula"
          />
        </div>
      </div>
    </Section>
  );
}



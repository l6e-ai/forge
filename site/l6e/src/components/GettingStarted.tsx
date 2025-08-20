import React from "react";
import Section from "./Section";
import CodeBlock from "./CodeBlock";

const steps = `# Install l6e AI
$ pip install l6e-forge

# Create and customize your agent
$ forge create agent my-agent --template=assistant
$ # Edit my-agent/agent.py with your logic

# Optional: Auto-pick local models (alpha; Apple Silicon optimized; Ollama only)
$ forge models doctor
$ forge models bootstrap --agent agents/my-agent --provider ollama

# Test locally
$ forge chat my-agent

# Package for deployment
$ forge package my-agent
📦 Created my-agent.l6e (portable agent)

# Deploy anywhere
$ forge deploy my-agent.l6e
🚀 Agent running locally`;

export default function GettingStarted() {
  return (
    <Section id="getting-started" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-4">Deploy Your First AI Agent</h2>
      <p className="text-white/70 max-w-2xl mb-6">
        l6e/forge helps you build portable AI agents with a local-first workflow. Use Auto Models to offload model selection and setup.
      </p>
      <CodeBlock code={steps} mode="bash" highlight language="bash" themeName="dracula" />
    </Section>
  );
}



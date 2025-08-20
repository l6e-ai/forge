import React from "react";
import Section from "./Section";
import CodeBlock from "./CodeBlock";

const steps = `# Install l6e Forge
$ pip install l6e-forge

# Create and customize your agent
$ forge create agent my-agent --template=assistant
$ # Edit agents/my-agent/agent.py with your logic

# Optional: Auto-pick local models (alpha; Apple Silicon optimized; Ollama only)
$ forge models doctor
$ forge models bootstrap --agent agents/my-agent --provider ollama

# Test locally
$ forge chat my-agent

# Package for distribution
$ forge pkg build agents/my-agent -o dist
📦 Created dist/my-agent-0.1.0.l6e (portable agent)

# Install into another workspace (e.g., your VPC or another machine)
$ forge pkg install dist/my-agent-0.1.0.l6e -w /path/to/workspace

# Run on your stack (local or internal cloud)
$ forge up
🚀 Stack running locally`;

export default function GettingStarted() {
  return (
    <Section id="getting-started" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-4">Deploy Your First AI Agent</h2>
      <p className="text-white/70 max-w-2xl mb-6">
        l6e/forge helps you build portable AI agents with a local-first workflow. Keep sensitive data on your own infrastructure—developer machines or inside your VPC. Use Auto Models to offload model selection and setup.
      </p>
      <CodeBlock code={steps} mode="bash" highlight language="bash" themeName="dracula" />
    </Section>
  );
}



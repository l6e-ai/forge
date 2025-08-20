"use client";

import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import Section from "../Section";
import Button from "../Button";
import CodeBlock from "../CodeBlock";

type Runner = "ollama" | "lmstudio";

type DemoStep = {
  id: string;
  title: string;
  command?: (runner: Runner) => string;
  output?: (runner: Runner) => string;
  code?: { language: "python" | "bash" | "toml"; snippet: string };
};

const steps: DemoStep[] = [
  {
    id: "install",
    title: "Install CLI",
    command: () => "pip install l6e-forge",
    output: () => "Successfully installed l6e-forge",
  },
  {
    id: "create",
    title: "Create an agent",
    command: (runner) =>
      `forge create agent my-agent --provider ${runner} --model ${runner === "ollama" ? "llama3.2:3b" : "phi3"}`,
    output: () => "Scaffolded my-agent/ with templates",
  },
  {
    id: "dev",
    title: "Validate dev setup",
    command: () => "forge dev --check",
    output: () => "Dev mode ready: workspace validated.",
  },
  {
    id: "chat",
    title: "Chat locally",
    command: () => "forge chat my-agent -m \"Hello\"",
    output: () => "assistant: Hello! How can I help you today?",
  },
  {
    id: "package",
    title: "Package",
    command: () => "forge pkg build agents/my-agent -o dist",
    output: () => "📦 Created dist/my-agent-0.1.0.l6e",
  },
  {
    id: "deploy",
    title: "Deploy",
    command: () => "forge up",
    output: () => "🚀 Stack running locally (personal-scale)",
  },
];

function useTypewriter(text: string, speed = 18) {
  const [display, setDisplay] = React.useState("");
  React.useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setDisplay(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
  }, [text, speed]);
  return display;
}

export default function DemoSection() {
  const [runner, setRunner] = React.useState<Runner>("ollama");
  const [index, setIndex] = React.useState(0);
  const step = steps[index];
  const command = step.command ? step.command(runner) : "";
  const typed = useTypewriter(command, 10);

  const next = () => setIndex((i) => Math.min(i + 1, steps.length - 1));
  const prev = () => setIndex((i) => Math.max(i - 1, 0));
  const replay = () => setIndex((i) => i);

  return (
    <Section className="py-16">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight">From install to deploy in minutes</h2>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-white/60">Runner:</span>
          <button
            className={`px-3 h-8 rounded ${runner === "ollama" ? "bg-white/15" : "bg-white/5"}`}
            onClick={() => setRunner("ollama")}
          >
            Ollama
          </button>
          <button
            className={`px-3 h-8 rounded ${runner === "lmstudio" ? "bg-white/15" : "bg-white/5"}`}
            onClick={() => setRunner("lmstudio")}
          >
            LM Studio
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <div>
          <div className="mb-3 text-sm text-white/70">Step {index + 1} / {steps.length} • {step.title}</div>
          <CodeBlock code={`$ ${typed}`} mode="bash" highlight language="bash" themeName="dracula" />
          {typed.length === command.length && step.output && (
            <AnimatePresence>
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
                <CodeBlock code={step.output(runner)} highlight language="bash" themeName="dracula" copy={false} />
              </motion.div>
            </AnimatePresence>
          )}
          <div className="mt-3 flex items-center gap-2">
            <Button variant="secondary" onClick={prev}>Prev</Button>
            <Button variant="primary" onClick={next}>Next</Button>
            <Button variant="outline" onClick={replay}>Replay</Button>
          </div>
        </div>
      </div>
      <div className="mt-6">
        <Button href="/docs" variant="outline">View full documentation</Button>
      </div>
    </Section>
  );
}



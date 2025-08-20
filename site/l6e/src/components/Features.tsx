import React from "react";
import Section from "./Section";

const features = [
  {
    title: "🤖 Auto Models (alpha)",
    body: "One command picks and installs the right OSS model for your hardware. Apple Silicon optimized. Ollama today; more soon.",
  },
  {
    title: "📦 Portable Agents",
    body: "Ship a single portable package and run it anywhere—dev to prod.",
  },
  {
    title: "🏠 Local-first",
    body: "Run on your machine with zero required cloud services and private data by default.",
  },
  {
    title: "🔧 Fast Dev Loop",
    body: "Hot reload, instant testing, and a focused CLI to move fast.",
  },
  {
    title: "🎯 Ready-made Templates",
    body: "Start from proven assistants, coding, and research patterns—customize in minutes.",
  },
  {
    title: "🧩 Pluggable Runners",
    body: "Use LM Studio or Ollama out of the box. llama.cpp support is coming soon.",
  },
  {
    title: "🔌 Interfaces over rewrites",
    body: "Adapt existing agents or frameworks (e.g., LangChain) without rebuilding your codebase.",
  },
];

export default function Features() {
  return (
    <Section id="features" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-8">Highlights</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((f) => (
          <div key={f.title} className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
            <p className="text-white/70 text-sm">{f.body}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}



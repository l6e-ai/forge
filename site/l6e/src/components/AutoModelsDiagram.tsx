import React from "react";

function Arrow() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-white/40">
      <path d="M5 12h14M13 5l7 7-7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

type CardProps = {
  title: string;
  lines: string[];
};

function Card({ title, lines }: CardProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 min-h-[92px]">
      <div className="text-sm font-semibold mb-1">{title}</div>
      <ul className="text-xs text-white/70 leading-relaxed list-disc pl-4">
        {lines.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>
    </div>
  );
}

export default function AutoModelsDiagram() {
  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-[760px] grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-3">
        <Card title="Detect" lines={["OS, CPU, RAM, GPU/VRAM", "Local runners (Ollama)", "Internet availability"]} />
        <Arrow />
        <Card title="Recommend" lines={["Choose chat + embedding", "Apple Silicon-optimized", "Curated defaults"]} />
        <Arrow />
        <Card title="Bootstrap" lines={["Pull models via Ollama", "Verify availability", "Update agent config"]} />
      </div>
      <div className="mt-3 text-xs text-white/50">Flow: detect → recommend → bootstrap. Runs automatically on first start if models are missing.</div>
    </div>
  );
}



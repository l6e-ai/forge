import React from "react";
import Section from "./Section";

const features = [
  {
    title: "📦 Portable Agents",
    body: "Package agents that run anywhere. Build once, deploy everywhere.",
  },
  {
    title: "🏠 Local Infrastructure",
    body: "Run on your hardware with complete data sovereignty.",
  },
  {
    title: "🔧 Developer Experience",
    body: "Hot reload, instant testing, rich tooling. Build fast.",
  },
  {
    title: "🎯 Template Ecosystem",
    body: "Start with proven patterns for assistants, coding, research, and more.",
  },
  {
    title: "⚡ Performance",
    body: "Blazing fast on modern hardware with local models.",
  },
  {
    title: "🔒 Enterprise Ready",
    body: "Secure packaging, audit trails, and compliance friendly.",
  },
];

export default function Features() {
  return (
    <Section id="features" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-8">Key Capabilities</h2>
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



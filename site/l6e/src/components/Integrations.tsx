import React from "react";
import Image from "next/image";
import Section from "./Section";
import StackIcon from "./icons/Stack";

const items = [
  {
    name: "LM Studio",
    description:
      "Local model runner with desktop UX. Use alongside l6e/forge for zero-cloud dev.",
    href: "https://lmstudio.ai",
    logo: "/providers/lm_studio_logo.png",
  },
  {
    name: "Ollama",
    description:
      "Pull and run open LLMs locally. Multi-model workflows supported.",
    href: "https://ollama.com",
    logo: "/providers/ollama_logo.png",
  },
  {
    name: "llama.cpp (coming soon)",
    description:
      "Lightweight, CPU/GPU-friendly runner. Bring-your-own binaries and configs.",
    href: "https://github.com/ggerganov/llama.cpp",
    logo: "/providers/llama1-logo.png",
  },
  {
    name: "Your stack",
    description:
      "Interfaces over rewrites. Adapt existing agents or frameworks (LangChain, custom services) into your cloud when you need it.",
    href: "/docs/adapters",
    logo: null,
  },
];

export default function Integrations() {
  return (
    <Section id="integrations" className="py-16">
      <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-8">Pluggable Runners & Interop</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {items.map((it) => (
          <a
            key={it.name}
            href={it.href}
            target={it.href.startsWith("http") ? "_blank" : undefined}
            rel={it.href.startsWith("http") ? "noreferrer" : undefined}
            className="rounded-lg border border-white/10 bg-white/5 p-5 hover:bg-white/10 transition-colors"
          >
            <div className="flex items-center gap-3 mb-2">
              {it.logo ? (
                <Image
                  src={it.logo}
                  alt={`${it.name} logo`}
                  width={28}
                  height={28}
                />
              ) : (
                <span className="text-white/80"><StackIcon /></span>
              )}
              <h3 className="text-lg font-semibold">{it.name}</h3>
            </div>
            <p className="text-white/70 text-sm">{it.description}</p>
            <div className="mt-3 text-xs text-white/60 underline underline-offset-4">Learn more</div>
          </a>
        ))}
      </div>
    </Section>
  );
}



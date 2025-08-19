"use client";

import React from "react";
import Link from "next/link";
import Button from "./Button";

export default function Nav() {
  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur supports-[backdrop-filter]:bg-black/40 border-b border-white/10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold">
          <span className="inline-block h-2 w-2 rounded-full bg-[#00ff88]" />
          <span>l6e AI</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm text-white/80">
          <Link href="/#features" className="hover:text-white">Features</Link>
          <Link href="/#getting-started" className="hover:text-white">Getting Started</Link>
          <Link href="/docs" className="hover:text-white">Docs</Link>
          <Link href="https://github.com/l6e-ai/agent-forge" target="_blank" rel="noopener noreferrer" className="hover:text-white">GitHub</Link>
          <Button href="https://github.com/l6e-ai/agent-forge" variant="primary">Get Started</Button>
        </nav>
        <div className="md:hidden">
          <Button href="https://github.com/l6e-ai/agent-forge" variant="primary">Get Started</Button>
        </div>
      </div>
    </header>
  );
}



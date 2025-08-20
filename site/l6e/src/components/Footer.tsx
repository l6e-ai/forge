import React from "react";
import Section from "./Section";

export default function Footer() {
  return (
    <Section className="py-10">
      <div className="border-t border-white/10 pt-6 text-sm text-white/60 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p>© {new Date().getFullYear()} l6e AI. Open Source.</p>
        <div className="flex items-center gap-4">
          <a href="https://github.com/l6e-ai/forge" target="_blank" rel="noreferrer" className="hover:text-white">GitHub</a>
          <a href="/docs" className="hover:text-white">Docs</a>
        </div>
      </div>
    </Section>
  );
}



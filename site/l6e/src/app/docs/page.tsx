import React from "react";
import Nav from "../../components/Nav";
import Section from "../../components/Section";
import Footer from "../../components/Footer";

export default function DocsPage() {
  return (
    <div className="min-h-screen font-sans bg-[#0a0a0a] text-white">
      <Nav />
      <main>
        <Section className="py-16">
          <h1 className="text-3xl font-bold mb-4">Documentation</h1>
          <p className="text-white/70 max-w-2xl">
            Full docs coming soon. In the meantime, visit our README and examples on GitHub.
          </p>
          <div className="mt-6">
            <a
              className="underline underline-offset-4 hover:text-white"
              href="https://github.com/l6e-ai/agent-forge"
              target="_blank"
              rel="noreferrer"
            >
              Open GitHub Repository
            </a>
          </div>
        </Section>
      </main>
      <Footer />
    </div>
  );
}



"use client";

import React from "react";
import clsx from "clsx";

type CodeBlockProps = {
  code: string;
  className?: string;
  copy?: boolean;
  mode?: "text" | "bash";
  copyTransform?: (displayed: string) => string;
};

function defaultBashCopyTransform(displayed: string): string {
  return displayed
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.startsWith("$ "))
    .map((line) => {
      const withoutPrompt = line.slice(2);
      const commentIndex = withoutPrompt.indexOf(" # ");
      const content = commentIndex >= 0 ? withoutPrompt.slice(0, commentIndex) : withoutPrompt;
      const trimmed = content.trim();
      return trimmed.startsWith("#") ? "" : trimmed;
    })
    .filter((line) => line.length > 0)
    .join("\n");
}

export default function CodeBlock({ code, className, copy = true, mode = "text", copyTransform }: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);

  const onCopy = async () => {
    try {
      const toCopy = copyTransform
        ? copyTransform(code)
        : mode === "bash"
        ? defaultBashCopyTransform(code)
        : code;
      await navigator.clipboard.writeText(toCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // noop
    }
  };

  return (
    <div className={clsx("relative bg-black/60 border border-white/10 rounded-lg p-4 font-mono text-sm text-white/90", className)}>
      {copy && (
        <button
          onClick={onCopy}
          className={clsx(
            "absolute top-2 right-2 h-7 px-2 rounded-md text-xs",
            copied ? "bg-emerald-600/80" : "bg-white/10 hover:bg-white/20"
          )}
          aria-label="Copy code"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      )}
      <pre className="whitespace-pre-wrap leading-relaxed">{code}</pre>
    </div>
  );
}



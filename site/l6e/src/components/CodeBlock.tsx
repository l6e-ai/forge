"use client";

import React from "react";
import clsx from "clsx";
import { Highlight, themes } from "prism-react-renderer";
import type { Language, PrismTheme } from "prism-react-renderer";

type CodeBlockProps = {
  code: string;
  className?: string;
  copy?: boolean;
  mode?: "text" | "bash";
  copyTransform?: (displayed: string) => string;
  highlight?: boolean;
  language?: Language;
  themeName?:
    | "dracula"
    | "duotoneDark"
    | "duotoneLight"
    | "github"
    | "nightOwl"
    | "nightOwlLight"
    | "oceanicNext"
    | "palenight"
    | "shadesOfPurple"
    | "synthwave84"
    | "ultramin";
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

export default function CodeBlock({ code, className, copy = true, mode = "text", copyTransform, highlight = false, language = "tsx", themeName = "dracula" }: CodeBlockProps) {
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

  const themeMap = themes as Record<string, PrismTheme>;
  const selectedTheme: PrismTheme = themeMap[themeName] || themes.dracula;

  return (
    <div className={clsx("relative bg-[#0c0c0c] border border-white/10 rounded-lg p-4 font-mono text-[13px] leading-relaxed text-white/90", className)}>
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
      {highlight ? (
        <Highlight theme={selectedTheme} code={code} language={language}>
          {({ className: cl, style, tokens, getLineProps, getTokenProps }) => (
            <pre
              className={cl}
              style={{
                ...style,
                background: "transparent",
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                wordBreak: "break-word",
              }}
            >
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })}>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token })} />
                  ))}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      ) : (
        <pre className="whitespace-pre-wrap leading-relaxed">{code}</pre>
      )}
    </div>
  );
}



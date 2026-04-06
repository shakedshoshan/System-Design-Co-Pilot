"use client";

import { useEffect, useId, useRef, useState } from "react";

type Props = { code: string };

export function MermaidBlock({ code }: Props) {
  const id = useId().replace(/:/g, "");
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    void import("mermaid").then(({ default: mermaid }) => {
      if (cancelled || !containerRef.current) return;
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "neutral",
        fontFamily: "inherit",
      });
      const renderId = `mermaid-${id}-${Math.random().toString(36).slice(2, 9)}`;
      mermaid
        .render(renderId, code)
        .then(({ svg }) => {
          if (!cancelled && containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch((e: unknown) => {
          if (!cancelled) {
            setError(e instanceof Error ? e.message : "Mermaid render failed");
          }
        });
    });

    return () => {
      cancelled = true;
    };
  }, [code, id]);

  if (error) {
    return (
      <pre className="overflow-x-auto rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
        <code>{code}</code>
        <p className="mt-2 text-amber-700 dark:text-amber-300">{error}</p>
      </pre>
    );
  }

  return (
    <div
      ref={containerRef}
      className="mermaid-root my-4 flex justify-center overflow-x-auto rounded-lg border border-black/10 bg-white/80 p-4 dark:border-white/10 dark:bg-black/40"
      aria-label="Diagram"
    />
  );
}

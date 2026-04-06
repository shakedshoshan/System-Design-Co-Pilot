"use client";

import type { ComponentPropsWithoutRef } from "react";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { MermaidBlock } from "@/components/diagrams/MermaidBlock";

type CodeProps = ComponentPropsWithoutRef<"code"> & {
  inline?: boolean;
  node?: unknown;
};

function CodeComponent({ inline, className, children, ...rest }: CodeProps) {
  if (inline) {
    return (
      <code
        className="rounded bg-black/[0.06] px-1 py-0.5 font-mono text-[0.9em] dark:bg-white/10"
        {...rest}
      >
        {children}
      </code>
    );
  }
  const match = /language-(\w+)/.exec(className ?? "");
  const lang = match?.[1];
  const text = String(children).replace(/\n$/, "");
  if (lang === "mermaid") {
    return <MermaidBlock code={text} />;
  }
  return (
    <code
      className={`block overflow-x-auto rounded-lg bg-black/[0.06] p-3 font-mono text-sm dark:bg-white/10 ${className ?? ""}`}
      {...rest}
    >
      {children}
    </code>
  );
}

const components: Components = {
  code: CodeComponent,
};

type Props = { content: string; className?: string };

export function SafeMarkdown({ content, className }: Props) {
  return (
    <div
      className={`space-y-3 text-sm leading-relaxed [&_h1]:mb-2 [&_h1]:text-xl [&_h1]:font-semibold [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h3]:font-medium [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:pl-5 [&_a]:text-blue-600 [&_a]:underline dark:[&_a]:text-blue-400 [&_p]:whitespace-pre-wrap [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-black/20 [&_th]:bg-black/5 [&_th]:p-2 [&_td]:border [&_td]:border-black/20 [&_td]:p-2 dark:[&_th]:border-white/20 dark:[&_td]:border-white/20 ${className ?? ""}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

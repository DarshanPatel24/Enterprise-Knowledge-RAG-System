"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import "highlight.js/styles/github.css";

/**
 * Render assistant response text as GitHub-flavoured Markdown.
 *
 * Tables and lists come from `remark-gfm`; fenced code blocks are highlighted
 * by `rehype-highlight` (bundled locally, no external requests). Element styling
 * is applied through Tailwind utility classes so tables and code blocks render
 * without layout breakage.
 */
const COMPONENTS: Components = {
  a: ({ children, href }) => (
    <a
      href={href}
      className="text-primary underline underline-offset-2"
      rel="noreferrer noopener"
      target="_blank"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => (
    <ul className="my-2 ml-5 list-disc space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-2 ml-5 list-decimal space-y-1">{children}</ol>
  ),
  p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
  h1: ({ children }) => <h1 className="mb-2 mt-3 text-xl font-semibold">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-3 text-lg font-semibold">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1 mt-2 text-base font-semibold">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-border pl-3 text-muted-foreground">
      {children}
    </blockquote>
  ),
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded-md border bg-muted p-3 text-xs">
      {children}
    </pre>
  ),
  code: ({ className, children }) => {
    const isBlock = /language-/.test(className ?? "");
    if (isBlock) {
      return <code className={className}>{children}</code>;
    }
    return (
      <code className="rounded bg-muted px-1 py-0.5 text-[0.85em]">{children}</code>
    );
  },
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border bg-muted px-2 py-1 text-left font-semibold">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-border px-2 py-1 align-top">{children}</td>
  ),
};

export function MarkdownContent({ content }: { content: string }): React.JSX.Element {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={COMPONENTS}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

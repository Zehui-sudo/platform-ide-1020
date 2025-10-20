'use client';

import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { cn } from '@/lib/utils';
import { InteractiveCodeBlock } from './InteractiveCodeBlock';
import { ContentStaticCodeBlock } from './ContentStaticCodeBlock';
import { MermaidDiagram } from './MermaidDiagram';
import { resolveLegacyUrl } from '@/utils/contentPath';
import { WebInteractiveCodeBlock } from './WebInteractiveCodeBlock';

// Import KaTeX CSS for math rendering
import 'katex/dist/katex.min.css';

interface EnhancedMarkdownRendererProps {
  content: string;
  className?: string;
  enableMath?: boolean;
  enableGfm?: boolean;
  fontSize?: number;
  // Used to namespace interactive code block state per section
  sectionScopeId?: string;
  // Index of this markdown block inside the current section's contentBlocks
  markdownIndex?: number;
}

export function EnhancedMarkdownRenderer({
  content,
  className,
  enableMath = true,
  enableGfm = true,
  fontSize = 16,
  sectionScopeId,
  markdownIndex = 0,
}: EnhancedMarkdownRendererProps) {
  const plugins = useMemo(() => {
    const plugins = [];
    if (enableGfm) plugins.push(remarkGfm);
    if (enableMath) plugins.push(remarkMath);
    return plugins;
  }, [enableGfm, enableMath]);

  const rehypePlugins = useMemo(() => {
    const plugins = [];
    if (enableMath) plugins.push(rehypeKatex);
    return plugins;
  }, [enableMath]);

  const scaleFactor = fontSize / 16;

  // Counter for code block ordering within this markdown content
  let codeOrdinal = 0;

  return (
    <div
      className={cn("prose prose-sm dark:prose-invert max-w-none", className)}
      style={{ fontSize: `${fontSize}px` }}
      data-markdown-index={markdownIndex}
    >
      <ReactMarkdown
        remarkPlugins={plugins}
        rehypePlugins={rehypePlugins}
        components={{
          p: ({ node, children }) => {
            // Check if the paragraph contains a table. If so, render children directly.
            const hasTable = node?.children?.some(child => child.type === 'element' && child.tagName === 'table');
            if (hasTable) {
              return <>{children}</>;
            }
            // Default paragraph rendering with relative spacing
            return <p className="my-4 leading-relaxed">{children}</p>;
          },
          code: (rawProps) => {
            type CodeRendererProps = React.ComponentPropsWithoutRef<'code'> & {
              inline?: boolean;
              node?: unknown;
              children?: React.ReactNode;
            };
            const { node, inline, className, children, ...props } = rawProps as CodeRendererProps;
            const match = /language-(\w+(?:-\w+)?)/.exec(className || '');
            const codeContent = String(children).replace(/\n$/, '');

            if (inline || !match) {
              return (
                <code
                  className="bg-muted text-muted-foreground font-mono px-1.5 py-1 rounded-md"
                  style={{ fontSize: '0.875em' }}
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // Block-level code with language
            const langRaw = match[1].toLowerCase();

            // Interactive: python
            if (langRaw === 'interactive-python' || langRaw === 'python') {
              const position = (node as { position?: { start?: { line?: number; offset?: number }; end?: { offset?: number } } } | undefined)?.position;
              const sectionId = `md-${sectionScopeId || 'global'}-${position?.start?.line || 0}`;
              const startOffset = position?.start?.offset ?? -1;
              const endOffset = position?.end?.offset ?? -1;
              const thisOrdinal = codeOrdinal++;
              return (
                <div
                  className="my-6"
                  data-role="code-block"
                  data-code-ordinal={thisOrdinal}
                  data-section-id={sectionId}
                  data-markdown-index={markdownIndex}
                  data-start-offset={startOffset}
                  data-end-offset={endOffset}
                  data-language="python"
                >
                  <InteractiveCodeBlock
                    language="python"
                    initialCode={codeContent}
                    sectionId={sectionId}
                    fontSize={fontSize}
                  />
                </div>
              );
            }

            // Interactive Web Preview: JavaScript
            if (langRaw === 'interactive-javascript' || langRaw === 'javascript' || langRaw === 'js') {
              const position = (node as { position?: { start?: { line?: number; offset?: number }; end?: { offset?: number } } } | undefined)?.position;
              const sectionId = `md-${sectionScopeId || 'global'}-${position?.start?.line || 0}`;
              const startOffset = position?.start?.offset ?? -1;
              const endOffset = position?.end?.offset ?? -1;
              const thisOrdinal = codeOrdinal++;
              return (
                <div
                  className="my-6"
                  data-role="code-block"
                  data-code-ordinal={thisOrdinal}
                  data-section-id={sectionId}
                  data-markdown-index={markdownIndex}
                  data-start-offset={startOffset}
                  data-end-offset={endOffset}
                  data-language="javascript"
                >
                  <WebInteractiveCodeBlock
                    language="javascript"
                    initialCode={codeContent}
                    sectionId={sectionId}
                    fontSize={fontSize}
                  />
                </div>
              );
            }

            // Mermaid diagrams
            if (langRaw === 'mermaid') {
              return (
                <div className="my-6" data-role="mermaid-block" data-markdown-index={markdownIndex}>
                  <MermaidDiagram 
                    code={codeContent} 
                    fontSize={fontSize}
                    sectionId={sectionScopeId}
                    markdownIndex={markdownIndex}
                  />
                </div>
              );
            }

            // Interactive Web Preview: HTML
            if (langRaw === 'html') {
              const position = (node as { position?: { start?: { line?: number } } } | undefined)?.position;
              const sectionId = `md-${sectionScopeId || 'global'}-${position?.start?.line || 0}`;
              const thisOrdinal = codeOrdinal++;
              return (
                <div
                  className="my-6"
                  data-role="code-block"
                  data-code-ordinal={thisOrdinal}
                  data-section-id={sectionId}
                  data-markdown-index={markdownIndex}
                  data-language="html"
                >
                  <WebInteractiveCodeBlock
                    language="html"
                    initialCode={codeContent}
                    sectionId={sectionId}
                    fontSize={fontSize}
                  />
                </div>
              );
            }

            // Static code examples: jsx, tsx, others
            const staticLang =
              langRaw === 'jsx' ? 'jsx' :
              langRaw === 'tsx' ? 'tsx' :
              langRaw;

            return <ContentStaticCodeBlock language={staticLang} code={codeContent} fontSize={fontSize} />;
          },
          h1: ({ children }) => <h1 className="font-bold mt-8 mb-4 pb-2 border-b" style={{ fontSize: '2.5em' }}>{children}</h1>,
          h2: ({ children }) => <h2 className="font-semibold mt-10 mb-4 pb-2 border-b" style={{ fontSize: '2em' }}>{children}</h2>,
          h3: ({ children }) => <h3 className="font-semibold mt-8 mb-4" style={{ fontSize: '1.5em' }}>{children}</h3>,
          h4: ({ children }) => <h4 className="font-semibold mt-6 mb-4" style={{ fontSize: '1.25em' }}>{children}</h4>,
          h5: ({ children }) => <h5 className="font-semibold mt-4 mb-2" style={{ fontSize: '1.125em' }}>{children}</h5>,
          h6: ({ children }) => <h6 className="font-semibold mt-4 mb-2" style={{ fontSize: '1em' }}>{children}</h6>,
          a: ({ href, children }) => {
            // Rewrite legacy flat content links to new nested paths at runtime
            let newHref = href as string | undefined;

            try {
              if (typeof newHref === 'string') {
                // Case 1: /content/{legacyId}.md
                if (newHref.startsWith('/content/')) {
                  const legacy = newHref.replace(/^\/content\//, '').replace(/\.md$/i, '');
                  newHref = resolveLegacyUrl(legacy);
                }
                // Case 2: plain legacy id like "js-sec-...", "py-sec-...", "python-sec-...", "astro-..." or "astrology_index"
                else if (/^(js-|py-|python-sec-|astro-)|^astrology_index$/.test(newHref)) {
                  newHref = resolveLegacyUrl(newHref);
                }
              }
            } catch {
              // noop on rewrite failure, keep original href
            }

            return (
              <a
                href={newHref}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {children}
              </a>
            );
          },
          table: ({ children }) => (
            <div className="my-6 overflow-hidden rounded-lg border border-border">
              <div className="overflow-x-auto">
                <table className="w-full" style={{ fontSize: 'inherit' }}>
                  {children}
                </table>
              </div>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border-b border-border hover:bg-muted/50 last:border-b-0">{children}</tr>,
          th: ({ children }) => <th className="text-left font-semibold border-r border-border last:border-r-0" style={{ padding: `${0.75 * scaleFactor}rem` }}>{children}</th>,
          td: ({ children }) => <td className="border-r border-border last:border-r-0" style={{ padding: `${0.75 * scaleFactor}rem` }}>{children}</td>,
          blockquote: ({ children }) => <blockquote className="my-6 pl-4 border-l-4 border-primary bg-muted/50 italic py-2">{children}</blockquote>,
          ul: ({ children }) => <ul className="my-4 ml-6 list-disc space-y-2">{children}</ul>,
          ol: ({ children }) => <ol className="my-4 ml-6 list-decimal space-y-2">{children}</ol>,
          li: ({ children }) => <li className="pl-2">{children}</li>,
          hr: () => <hr className="my-8 border-border" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

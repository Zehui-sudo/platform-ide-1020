'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Copy, Check } from 'lucide-react';
import { CodeMirrorCodeBlock } from './CodeMirrorCodeBlock';

interface ContentStaticCodeBlockProps {
  language: string;
  code: string;
  fontSize?: number;
}

// Prose-friendly static code block for course content with lightweight toolbar
export function ContentStaticCodeBlock({ language, code, fontSize = 16 }: ContentStaticCodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const normalized = language.toLowerCase();
  const label = normalized.toUpperCase();
  const cmLanguage: 'javascript' | 'python' | 'jsx' | 'tsx' | 'html' | 'json' | 'http' | undefined =
    normalized === 'jsx' ? 'jsx'
    : normalized === 'tsx' ? 'tsx'
    : normalized === 'ts' || normalized === 'typescript' ? 'tsx'
    : normalized === 'json' ? 'json'
    : normalized === 'javascript' || normalized === 'js' ? 'javascript'
    : normalized === 'html' ? 'html'
    : normalized === 'http' ? 'http'
    : undefined;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // noop
    }
  };

  // 30 lines max height based on current font size with ~1.5 line-height
  const lineHeight = fontSize * 1.5;
  const maxHeightPx = Math.round(lineHeight * 30);

  return (
    <div
      className="my-6 w-full max-w-full rounded-md border bg-muted/30"
      data-role="content-static-code-block"
      data-language={language}
    >
      <div className="flex items-center justify-between px-2 py-1 border-b">
        <Badge variant="outline" className="text-[10px] uppercase">{label}</Badge>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2"
          title="复制代码"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        </Button>
      </div>

      <div
        className="w-full max-w-full overflow-y-auto"
        style={{ maxHeight: `${maxHeightPx}px` }}
      >
        {cmLanguage ? (
          <CodeMirrorCodeBlock
            value={code}
            language={cmLanguage}
            readOnly
            className="border-0"
            fontSize={fontSize}
            maxHeightPx={maxHeightPx}
          />
        ) : (
          <pre
            className="p-3 font-mono text-sm whitespace-pre-wrap break-words"
            style={{
              fontSize: `${fontSize * 0.875}px`,
              wordBreak: 'break-word',
              overflowWrap: 'anywhere',
            }}
          >
            <code>{code}</code>
          </pre>
        )}
      </div>
    </div>
  );
}

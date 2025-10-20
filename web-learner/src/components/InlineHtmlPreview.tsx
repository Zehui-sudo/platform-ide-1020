'use client';

import React, { useMemo, useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { ContentStaticCodeBlock } from './ContentStaticCodeBlock';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

type InlineHtmlPreviewProps = {
  code: string;
  fontSize?: number;
  defaultHeight?: number;
  includeTailwind?: boolean;
  forceMount?: boolean; // keep iframe mounted when collapsed
};

export function InlineHtmlPreview({
  code,
  fontSize = 16,
  defaultHeight = 260,
  includeTailwind = true,
  forceMount = false,
}: InlineHtmlPreviewProps) {
  // A key to force re-mount iframe on refresh
  const [refreshKey, setRefreshKey] = useState(0);

  const srcDoc = useMemo(() => {
    const isFullDoc = /<\s*!doctype|<\s*html\b/i.test(code);

    if (isFullDoc) {
      // If a full document is provided, try to inject Tailwind when requested
      if (!includeTailwind) return code;
      try {
        if (/<\s*head\b/i.test(code)) {
          return code.replace(
            /<\s*head\b([^>]*)>/i,
            (m) => `${m}\n<script src="https://cdn.tailwindcss.com"></script>`
          );
        }
        // If no head present, insert one
        return code.replace(
          /<\s*html\b([^>]*)>/i,
          (m) => `${m}\n<head>\n<script src="https://cdn.tailwindcss.com"></script>\n</head>`
        );
      } catch {
        return code;
      }
    }

    // Build a minimal HTML document
    const tailwind = includeTailwind ? '<script src="https://cdn.tailwindcss.com"></script>' : '';
    const baseCss = `
      html, body { height: 100%; }
      body { margin: 16px; background: #ffffff; color: #0a0a0a; }
      *, *::before, *::after { box-sizing: border-box; }
    `;

    return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    ${tailwind}
    <style>${baseCss}</style>
  </head>
  <body>
    ${code}
  </body>
</html>`;
  }, [code, includeTailwind]);

  return (
    <div className="my-6" data-role="inline-html-preview">
      <ContentStaticCodeBlock language="html" code={code} fontSize={fontSize} />

      <Accordion type="single" collapsible className="rounded-md border bg-muted/10">
        <AccordionItem value="preview">
          <AccordionTrigger className="px-3">
            <div className="flex w-full items-center justify-between pr-2">
              <span>预览（HTML）</span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-7 px-2"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setRefreshKey((k) => k + 1);
                  }}
                  title="刷新预览"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent {...(forceMount ? { forceMount: true } : {})}>
            <div
              className="w-full overflow-auto rounded-md border bg-background"
              style={{ height: `${defaultHeight}px`, resize: 'vertical' as const }}
            >
              <iframe
                key={refreshKey}
                title="inline-preview"
                className="w-full h-full"
                sandbox="allow-scripts allow-forms allow-modals"
                srcDoc={srcDoc}
              />
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

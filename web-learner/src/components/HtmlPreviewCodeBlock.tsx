'use client';

import React, { useMemo, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CodeMirrorCodeBlock } from './CodeMirrorCodeBlock';
import { Copy, Check, Eye, EyeOff, RefreshCw } from 'lucide-react';

type HtmlPreviewCodeBlockProps = {
  code: string;
  fontSize?: number;
  defaultHeight?: number;
  includeTailwind?: boolean;
};

export function HtmlPreviewCodeBlock({
  code,
  fontSize = 16,
  defaultHeight = 280,
  includeTailwind = true,
}: HtmlPreviewCodeBlockProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [copied, setCopied] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {}
  }, [code]);

  const srcDoc = useMemo(() => {
    const isFullDoc = /<\s*!doctype|<\s*html\b/i.test(code);

    if (isFullDoc) {
      if (!includeTailwind) return code;
      try {
        if (/<\s*head\b/i.test(code)) {
          return code.replace(
            /<\s*head\b([^>]*)>/i,
            (m) => `${m}\n<script src="https://cdn.tailwindcss.com"></script>`
          );
        }
        return code.replace(
          /<\s*html\b([^>]*)>/i,
          (m) => `${m}\n<head>\n<script src="https://cdn.tailwindcss.com"></script>\n</head>`
        );
      } catch {
        return code;
      }
    }

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
    <Card className="my-6">
      <CardHeader className="py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] uppercase">HTML</Badge>
            <CardTitle className="text-sm">代码</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-7 px-2"
              onClick={() => setRefreshKey((k) => k + 1)}
              title="刷新预览"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 px-2"
              title="复制代码"
            >
              {copied ? (
                <Check className="h-3 w-3" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <CodeMirrorCodeBlock
            value={code}
            language="html"
            readOnly
            className="border-0"
            fontSize={fontSize}
          />
          <div className="flex items-center justify-between">
            <Button
              type="button"
              size="sm"
              onClick={() => setShowPreview((v) => !v)}
              className="flex items-center gap-2"
            >
              {showPreview ? (
                <>
                  <EyeOff className="h-3 w-3" />
                  隐藏预览
                </>
              ) : (
                <>
                  <Eye className="h-3 w-3" />
                  预览
                </>
              )}
            </Button>
            <div className="text-xs text-muted-foreground">{code.length} 字符</div>
          </div>
        </div>

        {showPreview && (
          <div className="space-y-3 animate-in slide-in-from-bottom-2 duration-300">
            <div className="rounded-lg border bg-muted/50">
              <div className="border-b px-3 py-2 text-sm font-medium">预览结果</div>
              <div className="w-full overflow-auto" style={{ height: `${defaultHeight}px`, resize: 'vertical' as const }}>
                <iframe
                  key={refreshKey}
                  title="html-preview"
                  className="w-full h-full"
                  sandbox="allow-scripts allow-forms allow-modals"
                  srcDoc={srcDoc}
                />
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

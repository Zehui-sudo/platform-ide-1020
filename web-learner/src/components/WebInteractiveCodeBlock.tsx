'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLearningStore } from '@/store/learningStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { CodeMirrorCodeBlock } from './CodeMirrorCodeBlock';
import { Copy, Check, RotateCcw, Search, X, Eye, EyeOff, RefreshCw, AlertTriangle } from 'lucide-react';

type WebInteractiveCodeBlockProps = {
  language: 'html' | 'javascript';
  initialCode: string;
  sectionId: string;
  fontSize?: number;
  defaultHeight?: number;
  includeTailwind?: boolean;
};

export function WebInteractiveCodeBlock({
  language,
  initialCode,
  sectionId,
  fontSize = 16,
  defaultHeight = 280,
  includeTailwind = true,
}: WebInteractiveCodeBlockProps) {
  const userCode = useLearningStore((state) => state.userCodeSnippets[sectionId]);
  const updateUserCode = useLearningStore((state) => state.updateUserCode);

  const [code, setCode] = useState(userCode || initialCode);
  const [copied, setCopied] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showSearch, setShowSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Reset when the markdown-derived sectionId changes
    setCode(userCode || initialCode);
    setError('');
    setShowPreview(false);
  }, [sectionId, initialCode, userCode]);

  const handleCodeChange = useCallback((newCode: string) => {
    setCode(newCode);
  }, []);

  const handleCodeBlur = useCallback((newCode: string) => {
    updateUserCode(sectionId, newCode);
  }, [sectionId, updateUserCode]);

  const handleResetCode = () => {
    setCode(initialCode);
    updateUserCode(sectionId, initialCode);
    setError('');
    setRefreshKey((k) => k + 1);
  };

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {}
  };

  const handleSearchToggle = () => {
    setShowSearch((v) => !v);
    if (showSearch) setSearchTerm('');
  };

  const srcDoc = useMemo(() => {
    setError('');

    const baseCss = `
      html, body { height: 100%; }
      body { margin: 16px; background: #ffffff; color: #0a0a0a; }
      *, *::before, *::after { box-sizing: border-box; }
      .__error__ { color: #b91c1c; background: #fee2e2; padding: 8px 10px; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    `;

    const tailwind = includeTailwind ? '<script src="https://cdn.tailwindcss.com"></script>' : '';

    if (language === 'html') {
      const snippet = code || '';
      const isFullDoc = /<\s*!doctype|<\s*html\b/i.test(snippet);
      if (isFullDoc) {
        // Try to inject Tailwind
        try {
          if (!includeTailwind) return snippet;
          if (/<\s*head\b/i.test(snippet)) {
            return snippet.replace(/<\s*head\b([^>]*)>/i, (m) => `${m}\n${tailwind}\n<style>${baseCss}</style>`);
          }
          return snippet.replace(/<\s*html\b([^>]*)>/i, (m) => `${m}\n<head>\n${tailwind}\n<style>${baseCss}</style>\n</head>`);
        } catch {
          return snippet;
        }
      }

      return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    ${tailwind}
    <style>${baseCss}</style>
  </head>
  <body>
    ${snippet}
  </body>
</html>`;
    }

    // language === 'javascript': wrap inside a simple HTML scaffold and run script
    const jsCode = code || '';
    // A tiny error overlay to surface runtime errors inside iframe
    const errorOverlay = `
      <script>
        window.addEventListener('error', function(e) {
          var pre = document.createElement('pre');
          pre.className = '__error__';
          pre.textContent = 'Error: ' + (e.error && e.error.message ? e.error.message : e.message);
          document.body.insertBefore(pre, document.body.firstChild);
        });
      </script>`;

    return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    ${tailwind}
    <style>${baseCss}</style>
  </head>
  <body>
    <div id="app"></div>
    ${errorOverlay}
    <script>
    try {
      ${jsCode}
    } catch (e) {
      var pre = document.createElement('pre');
      pre.className = '__error__';
      pre.textContent = 'Error: ' + (e && e.message ? e.message : String(e));
      document.body.insertBefore(pre, document.body.firstChild);
    }
    </script>
  </body>
</html>`;
   
  }, [language, code, includeTailwind]);

  return (
    <Card className="my-6">
      <CardHeader className="py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] uppercase">{language.toUpperCase()}</Badge>
            <CardTitle className="text-sm">代码</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            {showSearch && (
              <div className="flex items-center gap-1">
                <input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索"
                  className="h-7 px-2 py-1 text-xs rounded border bg-background"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => { setSearchTerm(''); setShowSearch(false); }}
                  className="h-7 px-2"
                  title="关闭搜索"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            )}
            {!showSearch && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleSearchToggle}
                className="h-7 px-2"
                title="搜索"
              >
                <Search className="h-3 w-3" />
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleCopyCode}
              className="h-7 px-2"
              title="复制代码"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleResetCode}
              className="h-7 px-2 text-xs"
              title="重置为原始代码"
            >
              <RotateCcw className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="relative">
            <CodeMirrorCodeBlock
              value={code}
              onChange={handleCodeChange}
              onBlur={handleCodeBlur}
              language={language}
              className="border-0"
              searchTerm={searchTerm}
              enableSearch={showSearch}
              fontSize={fontSize}
            />
          </div>
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
                  渲染预览
                </>
              )}
            </Button>
            <div className="text-xs text-muted-foreground">{code.length} 字符</div>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {showPreview && (
          <div className="space-y-3 animate-in slide-in-from-bottom-2 duration-300">
            <div className="rounded-lg border bg-muted/50">
              <div className="border-b px-3 py-2 text-sm font-medium flex items-center justify-between">
                <span>预览结果</span>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="h-7 px-2"
                  onClick={() => setRefreshKey((k) => k + 1)}
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
              <div className="w-full overflow-auto" style={{ height: `${defaultHeight}px`, resize: 'vertical' as const }}>
                <iframe
                  key={refreshKey}
                  title={`web-preview-${sectionId}`}
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


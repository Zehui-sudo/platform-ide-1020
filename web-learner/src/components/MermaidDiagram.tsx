'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLearningStore } from '@/store/learningStore';

import type { MermaidToExcalidrawResult } from '@excalidraw/mermaid-to-excalidraw/dist/interfaces.js';
import type { BinaryFiles } from '@excalidraw/excalidraw/types';
import type { NonDeletedExcalidrawElement } from '@excalidraw/excalidraw/element/types';

type MermaidToExcalidrawModule = typeof import('@excalidraw/mermaid-to-excalidraw');
type ExcalidrawModule = typeof import('@excalidraw/excalidraw');

// Serialize mermaid parsing/conversion to avoid race conditions in SPA
let __mermaidParseLock: Promise<void> | null = null;
let __releaseMermaidParseLock: (() => void) | null = null;

async function withMermaidLock<T>(fn: () => Promise<T>): Promise<T> {
  while (__mermaidParseLock) {
    try {
      await __mermaidParseLock;
    } catch {
      // ignore
    }
  }
  __mermaidParseLock = new Promise<void>((resolve) => {
    __releaseMermaidParseLock = resolve;
  });
  try {
    return await fn();
  } finally {
    __releaseMermaidParseLock?.();
    __releaseMermaidParseLock = null;
    __mermaidParseLock = null;
  }
}

interface MermaidDiagramProps {
  code: string;
  fontSize?: number;
  sectionId?: string;
  markdownIndex?: number;
}

export function MermaidDiagram({ code, fontSize = 16, sectionId, markdownIndex }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewMarkup, setPreviewMarkup] = useState<string | null>(null);
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [fullSizeMarkup, setFullSizeMarkup] = useState<string | null>(null);
  const diagramId = useMemo(
    () => `mermaid-excalidraw-${Math.random().toString(36).slice(2)}`,
    [],
  );

  // Normalize Mermaid source以适配当前使用的 v10 解析器
  const normalizedCode = useMemo(() => {
    let src = code ?? '';
    // 1) Normalize EOL
    src = src.replace(/\r\n?|\u2028|\u2029/g, '\n');
    // 2) Remove trailing semicolons at EOL (Mermaid v11 stricter)
    src = src.replace(/;[ \t]*(?=\n|$)/g, '');

    // 2.5) Normalize HTML line breaks in labels to newlines to avoid parser quirks
    src = src.replace(/<br\s*\/?\s*>/gi, '\n');

    // 3) Convert quoted edge labels to pipe syntax
    //    A -- "text" --> B  =>  A -->|text| B
    //    A -. "text" .-> B  =>  A -.|text|.-> B
    //    A == "text" ==> B  =>  A ==>|text| B
    const edgePatterns: Array<[RegExp, string]> = [
      [/--\s*"([^"]*?)"\s*-->/g, '-->|$1|'],
      [/--\s*'([^']*?)'\s*-->/g, '-->|$1|'],
      [/-\.\s*"([^"]*?)"\s*\.->/g, '-.|$1|.->'],
      [/-\.\s*'([^']*?)'\s*\.->/g, '-.|$1|.->'],
      [/==\s*"([^"]*?)"\s*==>/g, '==>|$1|'],
      [/==\s*'([^']*?)'\s*==>/g, '==>|$1|'],
    ];
    for (const [re, repl] of edgePatterns) src = src.replace(re, repl);
    // Fix accidental duplicates like -->|text|-->
    src = src.replace(/-->\|([^|]*?)\|\s*-->/g, '-->|$1|');
    src = src.replace(/==>\|([^|]*?)\|\s*==>/g, '==>|$1|');
    // Trim spaces inside | label |
    src = src.replace(/\|\s+([^|]*?)\s+\|/g, (_m, p1) => `|${p1.trim()}|`);

    // 3.5) Quote edge pipe labels if they contain parentheses/colon and are unquoted
    //    B -->|返回 JSX (UI 描述)| C  =>  B -->|"返回 JSX (UI 描述)"| C
    src = src.replace(/(-->|-\.|==>)\|([^|]*?)\|/g, (_m, arrow, label) => {
      const t = String(label).trim();
      if (!t) return `${arrow}|${t}|`;
      if (t.startsWith('"') || t.startsWith("'")) return `${arrow}|${t}|`;
      return /[()：:]/.test(t) ? `${arrow}|"${t}"|` : `${arrow}|${t}|`;
    });

    // 4) Quote node labels inside square/curly brackets when they contain parentheses/colon
    //    C[更新状态: setCount(newState)] => C["更新状态: setCount(newState)"]
    //    D{DOM Diffing & Reconciliation (计算最小差异)} => D{"DOM Diffing & Reconciliation (计算最小差异)"}
    src = src.replace(/\b([A-Za-z0-9_:-]+)\[(?!["'])(?=[^\]\n]*[()：:])([^\]\n]*)\]/g, (_m, id, label) => `${id}["${label}"]`);
    src = src.replace(/\b([A-Za-z0-9_:-]+)\{(?!["'])(?=[^}\n]*[()：:])([^}\n]*)\}/g, (_m, id, label) => `${id}{"${label}"}`);

    // 5) Quote subgraph titles with parentheses/colon when not already quoted or using [title] form
    //    subgraph 普通变量 (无法触发更新)  =>  subgraph "普通变量 (无法触发更新)"
    //    subgraph State (触发UI更新)       =>  subgraph "State (触发UI更新)"
    src = src.replace(/^(\s*subgraph\s+)([^\n]+)$/gm, (full, pre, name) => {
      const trimmed = String(name).trim();
      if (!trimmed) return full;
      // already quoted
      if (trimmed.startsWith('"') || trimmed.startsWith("'")) return full;
      // has id [label] form -> keep as-is
      if (trimmed.includes('[')) return full;
      if (/[()：:]/.test(trimmed)) {
        return `${pre}"${trimmed}"`;
      }
      return full;
    });

    return src;
  }, [code]);

  useEffect(() => {
    let cancelled = false;

    async function renderExcalidrawSvg() {
      setError(null);
      const report = useLearningStore.getState().reportMermaidError;

      if (!normalizedCode.trim()) {
        setSvgMarkup(null);
        setFullSizeMarkup(null);
        return;
      }

      try {
        const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

        const importExcalidrawDeps = async () => {
          if (typeof window === 'undefined') {
            return Promise.all([
              import('@excalidraw/mermaid-to-excalidraw'),
              import('@excalidraw/excalidraw'),
            ]);
          }

          const win = window as typeof window & { Worker?: typeof Worker };
          const originalWorker = win.Worker;
          const shouldBypassSubsetWorker = process.env.NODE_ENV !== 'production' && typeof originalWorker !== 'undefined';
          let workerPatched = false;

          try {
            if (shouldBypassSubsetWorker) {
              try {
                // Temporarily disable Worker so Excalidraw skips subset-worker in dev.
                win.Worker = undefined as unknown as typeof Worker;
                workerPatched = true;
              } catch {
                workerPatched = false;
              }
            }

            return await Promise.all([
              import('@excalidraw/mermaid-to-excalidraw'),
              import('@excalidraw/excalidraw'),
            ]);
          } finally {
            if (workerPatched && typeof originalWorker !== 'undefined') {
              win.Worker = originalWorker;
            }
          }
        };

        const [mermaidModule, excalidrawModule] = await importExcalidrawDeps();

        if (cancelled) return;

        const { parseMermaidToExcalidraw } = mermaidModule as MermaidToExcalidrawModule;

        const scene = await withMermaidLock(async () => {
          // Some diagrams with HTML breaks in labels can cause downstream
          // converters to choke on undefined style objects. Try a sanitized
          // fallback if the first parse throws.
          const tryParse = async (src: string) =>
            (await parseMermaidToExcalidraw(src, {
              flowchart: { curve: 'linear' },
              themeVariables: {
                fontSize: `${fontSize}px`,
              },
              maxEdges: 500,
              maxTextSize: 50000,
            })) as MermaidToExcalidrawResult;

          try {
            return await tryParse(normalizedCode);
          } catch {
            const sanitized = normalizedCode.replace(/<br\s*\/?\s*>/gi, '\n');
            return await tryParse(sanitized);
          }
        });

        if (cancelled) return;

        const { convertToExcalidrawElements, exportToSvg } = excalidrawModule as ExcalidrawModule;
        if (typeof convertToExcalidrawElements !== 'function' || typeof exportToSvg !== 'function') {
          throw new Error('Excalidraw 导出模块不可用');
        }

        const binaryFiles = (scene.files ?? {}) as BinaryFiles;
        const convertedElements = convertToExcalidrawElements(
          scene.elements,
        ) as readonly NonDeletedExcalidrawElement[];
        const svgElement = await exportToSvg({
          elements: convertedElements,
          files: binaryFiles,
          appState: {
            theme: isDark ? 'dark' : 'light',
            viewBackgroundColor: 'transparent',
            exportBackground: false,
            shouldAddWatermark: false,
          },
          renderEmbeddables: false,
        });

        if (cancelled) return;

        const fullSizeSvg = svgElement.cloneNode(true) as SVGSVGElement;
        const serializer = new XMLSerializer();
        const fullSizeMarkup = serializer.serializeToString(fullSizeSvg);

        const SCALE = 0.5;
        const rawWidth = svgElement.getAttribute('width');
        const rawHeight = svgElement.getAttribute('height');
        const width = rawWidth ? Number.parseFloat(rawWidth) : Number.NaN;
        const height = rawHeight ? Number.parseFloat(rawHeight) : Number.NaN;

        if (!Number.isNaN(width) && !Number.isNaN(height)) {
          svgElement.style.width = `${width * SCALE}px`;
          svgElement.style.height = `${height * SCALE}px`;
        } else {
          svgElement.style.transformOrigin = 'top left';
          svgElement.style.transform = `scale(${SCALE})`;
          svgElement.style.height = 'auto';
        }

        svgElement.style.maxWidth = '100%';
        svgElement.style.display = 'block';
        svgElement.style.margin = '0 auto';

        const scaledMarkup = serializer.serializeToString(svgElement);

        if (cancelled) return;

        setSvgMarkup(scaledMarkup);
        setFullSizeMarkup(fullSizeMarkup);
      } catch (e) {
        if (cancelled) return;
        const message = e instanceof Error ? e.message : 'Mermaid 渲染失败';
        setError(message);
        setSvgMarkup(null);
        setFullSizeMarkup(null);
        report?.({
          sectionId,
          markdownIndex,
          error: message,
          code,
          normalizedCode,
          recovered: false,
          timestamp: Date.now(),
        });
      }
    }

    renderExcalidrawSvg();

    return () => {
      cancelled = true;
      setPreviewMarkup(null);
    };
  }, [code, normalizedCode, fontSize, sectionId, markdownIndex]);

  const closeOverlay = () => setPreviewMarkup(null);
  const handlePreviewClick = () => {
    if (fullSizeMarkup) {
      setPreviewMarkup(fullSizeMarkup);
    }
  };

  if (error) {
    return (
      <div className="rounded-lg border bg-muted/50">
        <div className="border-b px-3 py-2 text-sm font-medium">Mermaid 渲染失败</div>
        <pre className="p-3 text-xs text-destructive whitespace-pre-wrap">{error}</pre>
        <div className="border-t px-3 py-2 text-xs text-muted-foreground">原始内容：</div>
        <pre className="p-3 text-xs whitespace-pre-wrap overflow-x-auto">{code}</pre>
      </div>
    );
  }

  return (
    <>
      <div
        ref={containerRef}
        className="my-4 flex flex-col items-center"
        data-role="mermaid-diagram"
        data-diagram-id={diagramId}
        onClick={handlePreviewClick}
        title={fullSizeMarkup ? '点击查看大图' : undefined}
        style={{
          fontSize: `${fontSize}px`,
          cursor: fullSizeMarkup ? 'zoom-in' : 'default',
        }}
        dangerouslySetInnerHTML={svgMarkup ? { __html: svgMarkup } : undefined}
      />
      {previewMarkup ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={closeOverlay}
        >
          <div
            className="relative max-h-[90vh] max-w-[90vw] overflow-auto rounded-lg bg-white p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="absolute right-3 top-3 rounded-full bg-black/10 px-2 py-1 text-xs text-black hover:bg-black/20"
              onClick={closeOverlay}
            >
              ×
            </button>
            <div className="max-h-[80vh] overflow-auto">
              <div className="mx-auto" dangerouslySetInnerHTML={{ __html: previewMarkup }} />
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

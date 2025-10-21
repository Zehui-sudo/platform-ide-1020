#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

async function setupDomEnv() {
  const { JSDOM } = await import('jsdom');
  const dom = new JSDOM('<!doctype html><html><body></body></html>', {
    pretendToBeVisual: true,
    url: 'http://localhost',
  });
  const { window } = dom;

  // Expose globals expected by mermaid and excalidraw utils
  globalThis.window = window;
  globalThis.document = window.document;
  // Avoid assigning navigator on globalThis; window.navigator is sufficient
  globalThis.Element = window.Element;
  globalThis.HTMLElement = window.HTMLElement;
  globalThis.SVGElement = window.SVGElement;

  // requestAnimationFrame polyfill
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb) => setTimeout(() => cb(Date.now()), 0);
  }
  if (!window.cancelAnimationFrame) {
    window.cancelAnimationFrame = (id) => clearTimeout(id);
  }
  if (!globalThis.getComputedStyle) {
    globalThis.getComputedStyle = window.getComputedStyle.bind(window);
  }

  // btoa/atob polyfills for Node
  if (!window.btoa) {
    window.btoa = (str) => Buffer.from(String(str), 'binary').toString('base64');
  }
  if (!window.atob) {
    window.atob = (b64) => Buffer.from(String(b64), 'base64').toString('binary');
  }
  if (!globalThis.btoa) globalThis.btoa = window.btoa;
  if (!globalThis.atob) globalThis.atob = window.atob;

  // Minimal getBoundingClientRect and getBBox stubs for svg sizing
  if (!window.HTMLElement.prototype.getBoundingClientRect) {
    window.HTMLElement.prototype.getBoundingClientRect = function () {
      const w = Number.parseFloat(this.getAttribute?.('width') ?? '') || 800;
      const h = Number.parseFloat(this.getAttribute?.('height') ?? '') || 600;
      return { x: 0, y: 0, top: 0, left: 0, right: w, bottom: h, width: w, height: h, toJSON() {} };
    };
  }
  if (!window.SVGElement.prototype.getBBox) {
    // JSDOM lacks getBBox; return a rough box using width/height attrs if present
    window.SVGElement.prototype.getBBox = function () {
      const w = Number.parseFloat(this.getAttribute?.('width') ?? '') || 200;
      const h = Number.parseFloat(this.getAttribute?.('height') ?? '') || 80;
      return { x: 0, y: 0, width: w, height: h };
    };
  }

  // Prepare DOMPurify instance where Mermaid expects window.DOMPurify
  try {
    const mod = await import('dompurify');
    const createDOMPurify = mod.default || mod;
    const DOMPurify = createDOMPurify(window);
    window.DOMPurify = DOMPurify;
    globalThis.DOMPurify = DOMPurify;
  } catch {}

  return window;
}

// Locate the content root whether executed from repo root or from package dir
async function resolveContentRoot() {
  const candidates = [
    path.resolve(process.cwd(), 'public', 'content'),
    path.resolve(process.cwd(), 'web-learner', 'public', 'content'),
    path.resolve(process.cwd(), '..', 'web-learner', 'public', 'content'),
  ];
  for (const c of candidates) {
    try {
      const s = await fs.stat(c);
      if (s.isDirectory()) return c;
    } catch {}
  }
  throw new Error('Cannot locate public/content directory');
}

async function walk(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) await walk(full, out);
    else if (e.isFile() && e.name.endsWith('.md')) out.push(full);
  }
  return out;
}

// Iterate mermaid fenced code blocks (supports common misspelling `mermai`)
function* iterMermaidFences(content) {
  const re = /```(mermaid|mermai)\b[^\n]*\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(content)) !== null) {
    const lang = m[1];
    const inner = m[2];
    const start = m.index;
    const end = re.lastIndex;
    // Compute line numbers (1-based)
    const before = content.slice(0, start);
    const startLine = (before.match(/\n/g) || []).length + 1;
    const blockLines = content.slice(start, end);
    const endLine = startLine + (blockLines.match(/\n/g) || []).length;
    yield { lang, inner, start, end, startLine, endLine };
  }
}

// Normalization mirroring src/components/MermaidDiagram.tsx
function normalizeMermaidSource(src) {
  let out = src ?? '';
  // 1) Normalize EOL
  out = out.replace(/\r\n?|\u2028|\u2029/g, '\n');
  // 2) Remove trailing semicolons at EOL
  out = out.replace(/;[ \t]*(?=\n|$)/g, '');
  // 2.5) Normalize HTML line breaks in labels to newlines
  out = out.replace(/<br\s*\/?\s*>/gi, '\n');
  // 3) Convert quoted edge labels to pipe syntax
  const edgePatterns = [
    [/--\s*"([^"]*?)"\s*-->/g, '-->|$1|'],
    [/--\s*'([^']*?)'\s*-->/g, '-->|$1|'],
    [/-\.\s*"([^"]*?)"\s*\.->/g, '-.|$1|.->'],
    [/-\.\s*'([^']*?)'\s*\.->/g, '-.|$1|.->'],
    [/==\s*"([^"]*?)"\s*==>/g, '==>|$1|'],
    [/==\s*'([^']*?)'\s*==>/g, '==>|$1|'],
  ];
  for (const [re, repl] of edgePatterns) out = out.replace(re, repl);
  // Fix accidental duplicates like -->|text|-->
  out = out.replace(/-->\|([^|]*?)\|\s*-->/g, '-->|$1|');
  out = out.replace(/==>\|([^|]*?)\|\s*==>/g, '==>|$1|');
  // Trim spaces inside | label |
  out = out.replace(/\|\s+([^|]*?)\s+\|/g, (_m, p1) => `|${String(p1).trim()}|`);
  // 3.5) Quote edge pipe labels if they contain parentheses/colon and are unquoted
  out = out.replace(/(-->|-\.|==>)\|([^|]*?)\|/g, (_m, arrow, label) => {
    const t = String(label).trim();
    if (!t) return `${arrow}|${t}|`;
    if (t.startsWith('"') || t.startsWith("'")) return `${arrow}|${t}|`;
    return /[()：:]/.test(t) ? `${arrow}|"${t}"|` : `${arrow}|${t}|`;
  });
  // 4) Quote node labels inside []/{} when they contain parentheses/colon
  out = out.replace(/\b([A-Za-z0-9_:-]+)\[(?!["'])(?=[^\]\n]*[()：:])([^\]\n]*)\]/g, (_m, id, label) => `${id}["${label}"]`);
  out = out.replace(/\b([A-Za-z0-9_:-]+)\{(?!["'])(?=[^}\n]*[()：:])([^}\n]*)\}/g, (_m, id, label) => `${id}{"${label}"}`);
  // 5) Quote subgraph titles with parentheses/colon when not already quoted or using [title]
  out = out.replace(/^(\s*subgraph\s+)([^\n]+)$/gm, (full, pre, name) => {
    const trimmed = String(name).trim();
    if (!trimmed) return full;
    if (trimmed.startsWith('"') || trimmed.startsWith("'")) return full;
    if (trimmed.includes('[')) return full;
    if (/[()：:]/.test(trimmed)) return `${pre}"${trimmed}"`;
    return full;
  });
  return out;
}

async function parseWithMermaidToExcalidraw(src, { fontSizePx = 16 } = {}) {
  // Ensure DOM before loading mermaid/excalidraw pipeline
  await setupDomEnv();
  const { parseMermaidToExcalidraw } = await import('@excalidraw/mermaid-to-excalidraw');
  const options = {
    flowchart: { curve: 'linear' },
    themeVariables: { fontSize: `${fontSizePx}px` },
    maxEdges: 500,
    maxTextSize: 50000,
  };
  return await parseMermaidToExcalidraw(src, options);
}

async function tryFullPipeline(normalized, { fontSizePx = 16 } = {}) {
  // Validate that mermaid-to-excalidraw can parse + convert to skeleton elements
  const scene = await parseWithMermaidToExcalidraw(normalized, { fontSizePx });
  if (!scene || !scene.elements) throw new Error('Empty scene');
  const count = Array.isArray(scene.elements) ? scene.elements.length : 0;
  return { elementsCount: count };
}

async function main() {
  const ROOT = await resolveContentRoot();
  const files = await walk(ROOT);

  const failures = [];
  let total = 0;
  let parsed = 0;

  for (const file of files) {
    const content = await fs.readFile(file, 'utf8');
    let idx = 0;
    for (const f of iterMermaidFences(content)) {
      idx += 1;
      total += 1;
      const raw = f.inner;
      const normalized = normalizeMermaidSource(raw);
      try {
        // Mirror MermaidDiagram.tsx: try normalized; on failure, try sanitized <br> removal again
        try {
          await tryFullPipeline(normalized, { fontSizePx: 16 });
          parsed += 1;
        } catch (inner) {
          const sanitized = normalized.replace(/<br\s*\/?\s*>/gi, '\n');
          await tryFullPipeline(sanitized, { fontSizePx: 16 });
          parsed += 1;
        }
      } catch (e) {
        failures.push({
          file,
          code: raw,
          error: e instanceof Error ? e.message : String(e),
        });
      }
    }
  }

  const outDir = path.resolve(process.cwd(), 'output');
  try { await fs.mkdir(outDir, { recursive: true }); } catch {}
  const outPath = path.join(outDir, 'mermaid-render-errors.json');
  await fs.writeFile(outPath, JSON.stringify(failures, null, 2), 'utf8');

  console.log(`Validated ${total} Mermaid block(s). Parsed OK: ${parsed}. Failures: ${failures.length}.`);
  if (failures.length) {
    console.log(`Detailed failures written to ${path.relative(process.cwd(), outPath)}`);
  } else {
    console.log('All Mermaid blocks validated against parse+convert pipeline.');
  }
}

main().catch((e) => {
  console.error('validate-mermaid-render failed:', e);
  process.exit(1);
});

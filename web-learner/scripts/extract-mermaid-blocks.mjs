#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

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

// Heuristic normalization mirroring the front-end MermaidDiagram component
function normalizeMermaidSource(src) {
  let out = src ?? '';
  out = out.replace(/\r\n?|\u2028|\u2029/g, '\n');
  out = out.replace(/;[ \t]*(?=\n|$)/g, '');
  out = out.replace(/<br\s*\/?\s*>/gi, '\n');
  const patterns = [
    [/--\s*"([^"]*?)"\s*-->/g, '-->|$1|'],
    [/--\s*'([^']*?)'\s*-->/g, '-->|$1|'],
    [/-\.\s*"([^"]*?)"\s*\.->/g, '-.|$1|.->'],
    [/-\.\s*'([^']*?)'\s*\.->/g, '-.|$1|.->'],
    [/==\s*"([^"]*?)"\s*==>/g, '==>|$1|'],
    [/==\s*'([^']*?)'\s*==>/g, '==>|$1|'],
  ];
  for (const [re, repl] of patterns) out = out.replace(re, repl);
  out = out.replace(/-->\|([^|]*?)\|\s*-->/g, '-->|$1|');
  out = out.replace(/==>\|([^|]*?)\|\s*==>/g, '==>|$1|');
  out = out.replace(/\|\s+([^|]*?)\s+\|/g, (_m, p1) => `|${String(p1).trim()}|`);
  out = out.replace(/(-->|-\.|==>)\|([^|]*?)\|/g, (_m, arrow, label) => {
    const t = String(label).trim();
    if (!t) return `${arrow}|${t}|`;
    if (t.startsWith('"') || t.startsWith("'")) return `${arrow}|${t}|`;
    return /[()：:]/.test(t) ? `${arrow}|"${t}"|` : `${arrow}|${t}|`;
  });
  out = out.replace(/\b([A-Za-z0-9_:-]+)\[(?!["'])(?=[^\]\n]*[()：:])([^\]\n]*)\]/g, (_m, id, label) => `${id}["${label}"]`);
  out = out.replace(/\b([A-Za-z0-9_:-]+)\{(?!["'])(?=[^}\n]*[()：:])([^}\n]*)\}/g, (_m, id, label) => `${id}{"${label}"}`);
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

async function parseWithMermaidToExcalidraw(src) {
  // Lazy import to avoid ESM resolution cost when not needed
  const { parseMermaidToExcalidraw } = await import('@excalidraw/mermaid-to-excalidraw');
  const options = {
    flowchart: { curve: 'linear' },
    themeVariables: { fontSize: '16px' },
    maxEdges: 500,
    maxTextSize: 50000,
  };
  return await parseMermaidToExcalidraw(src, options);
}

async function main() {
  const ROOT = await resolveContentRoot();
  const files = await walk(ROOT);

  const allBlocks = [];
  const parseErrors = [];
  let totalBlocks = 0;
  let misspellFences = 0;

  for (const file of files) {
    const content = await fs.readFile(file, 'utf8');
    if (/```mermai\b/.test(content)) misspellFences += (content.match(/```mermai\b/g) || []).length;
    let idx = 0;
    for (const f of iterMermaidFences(content)) {
      idx += 1;
      totalBlocks += 1;
      const raw = f.inner;
      const normalized = normalizeMermaidSource(raw);
      const record = {
        file,
        blockIndex: idx,
        startLine: f.startLine,
        endLine: f.endLine,
        lang: f.lang,
        raw,
        normalized,
      };
      allBlocks.push(record);
      try {
        // Try parse with normalized source, mirroring front-end
        await parseWithMermaidToExcalidraw(normalized);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        parseErrors.push({ file, blockIndex: idx, startLine: f.startLine, endLine: f.endLine, error: message });
      }
    }
  }

  const outDir = path.resolve(process.cwd(), 'output');
  try { await fs.mkdir(outDir, { recursive: true }); } catch {}
  const blocksPath = path.join(outDir, 'mermaid-blocks.json');
  const errorsPath = path.join(outDir, 'mermaid-parse-errors.json');
  await fs.writeFile(blocksPath, JSON.stringify(allBlocks, null, 2), 'utf8');
  await fs.writeFile(errorsPath, JSON.stringify(parseErrors, null, 2), 'utf8');

  console.log(`Scanned ${files.length} files, found ${totalBlocks} mermaid blocks.`);
  if (misspellFences) console.log(`Also detected ${misspellFences} misspelled \`\`\`mermai fences.`);
  console.log(`Saved blocks to ${path.relative(process.cwd(), blocksPath)}`);
  if (parseErrors.length === 0) {
    console.log('All blocks parsed successfully with mermaid-to-excalidraw.');
  } else {
    console.log(`Detected ${parseErrors.length} parse error(s). Detailed report at ${path.relative(process.cwd(), errorsPath)}`);
  }
}

main().catch((e) => {
  console.error('extract-mermaid-blocks failed:', e);
  process.exit(1);
});


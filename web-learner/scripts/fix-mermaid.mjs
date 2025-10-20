#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

// Resolve content root whether executed from repo root or package dir
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

function normalizeMermaid(src) {
  let changed = false;
  let out = src.replace(/\r\n?|\u2028|\u2029/g, '\n');
  if (out !== src) changed = true;

  // 1) Remove trailing semicolons
  const out1 = out.replace(/;[ \t]*(?=\n|$)/g, '');
  if (out1 !== out) changed = true;
  out = out1;

  // 2) Convert quoted edge labels to pipe syntax
  const edgePatterns = [
    [/--\s*"([^"]*?)"\s*-->/g, '-->|$1|'],
    [/--\s*'([^']*?)'\s*-->/g, '-->|$1|'],
    [/-\.\s*"([^"]*?)"\s*\.->/g, '-.|$1|.->'],
    [/-\.\s*'([^']*?)'\s*\.->/g, '-.|$1|.->'],
    [/==\s*"([^"]*?)"\s*==>/g, '==>|$1|'],
    [/==\s*'([^']*?)'\s*==>/g, '==>|$1|'],
  ];
  for (const [re, repl] of edgePatterns) {
    const replaced = out.replace(re, repl);
    if (replaced !== out) changed = true;
    out = replaced;
  }

  // 3) Convert unquoted edge labels between arrows to pipe form
  const patterns2 = [
    [/--\s+([^"'|\n][^|\n]*?)\s+-->/g, (_m, label) => `-->|${label.trim()}|`],
    [/-\.\s+([^"'|\n][^|\n]*?)\s+\.->/g, (_m, label) => `-.|${label.trim()}|.->`],
    [/==\s+([^"'|\n][^|\n]*?)\s+==>/g, (_m, label) => `==>|${label.trim()}|`],
  ];
  for (const [re, repl] of patterns2) {
    const replaced = out.replace(re, repl);
    if (replaced !== out) changed = true;
    out = replaced;
  }

  // 4) Fix duplicate arrows like -->|text|-->
  const out2 = out
    .replace(/-->\|([^|]*?)\|\s*-->/g, '-->|$1|')
    .replace(/==>\|([^|]*?)\|\s*==>/g, '==>|$1|');
  if (out2 !== out) changed = true;
  out = out2;

  // 5) Trim label pipes
  const out3 = out.replace(/\|\s+([^|]*?)\s+\|/g, (_m, p1) => `|${p1.trim()}|`);
  if (out3 !== out) changed = true;
  out = out3;

  // 5.1) Quote pipe edge labels containing parentheses/colon if unquoted
  const out3b = out.replace(/(-->|-\.|==>)\|([^|]*?)\|/g, (_m, arrow, label) => {
    const t = String(label).trim();
    if (!t) return `${arrow}|${t}|`;
    if (t.startsWith('"') || t.startsWith("'")) return `${arrow}|${t}|`;
    if (/[()：:]/.test(t)) {
      changed = true;
      return `${arrow}|"${t}"|`;
    }
    return `${arrow}|${t}|`;
  });
  if (out3b !== out) changed = true;
  out = out3b;

  // 5.2) Replace HTML <br/> differently for sequenceDiagram
  const isSequence = /^\s*sequenceDiagram\b/m.test(out);
  if (isSequence) {
    // In sequence diagrams, prefer literal \n inside text instead of real newlines
    const out3c = out.replace(/<br\s*\/?\s*>/gi, '\\n');
    if (out3c !== out) changed = true;
    out = out3c;
  } else {
    // For other diagrams, normalize to real newlines to avoid parser quirks
    const out3c = out.replace(/<br\s*\/?\s*>/gi, '\n');
    if (out3c !== out) changed = true;
    out = out3c;
  }

  // 5.2c) sequenceDiagram: join stray wrapped lines back into message text using \n
  if (isSequence) {
    const lines = out.split('\n');
    const isDirectiveLine = (s) => /^(\s*)(sequenceDiagram|loop|alt|else|end|par|opt|critical|break|rect|autonumber|note|actor|participant|box|links|title|activate|deactivate|%%)/.test(s.trim());
    const isMessageLine = (s) => {
      const idx = s.indexOf(':');
      if (idx < 0) return false;
      const pre = s.slice(0, idx);
      return /(->>|-->>|->|-->|-x|x->|x>>|--x)/.test(pre);
    };
    let modified = false;
    const res = [];
    for (let i = 0; i < lines.length; i++) {
      let l = lines[i];
      if (isMessageLine(l)) {
        let acc = l;
        let j = i + 1;
        while (j < lines.length) {
          const nxt = lines[j];
          if (!nxt.trim()) break; // stop at blank line
          if (isDirectiveLine(nxt) || isMessageLine(nxt)) break;
          acc += '\\n' + nxt.trim();
          j++;
        }
        if (j !== i + 1) {
          modified = true;
          i = j - 1;
        }
        res.push(acc);
      } else {
        res.push(l);
      }
    }
    if (modified) {
      out = res.join('\n');
      changed = true;
    }
  }

  // 6) Quote node labels in [] and {} if contain parentheses/colon/[{ and unquoted
  const out4 = out
    .replace(/\b([A-Za-z0-9_:-]+)\[(?!["'])(?=[^\]\n]*[()：:\[\{])([^\]\n]*)\]/g, (_m, id, label) => `${id}["${label}"]`)
    .replace(/\b([A-Za-z0-9_:-]+)\{(?!["'])(?=[^}\n]*[()：:\[\{])([^}\n]*)\}/g, (_m, id, label) => `${id}{"${label}"}`);
  if (out4 !== out) changed = true;
  out = out4;

  // 6.1) Quote node labels in () if contain parentheses/colon/[{ and unquoted (supports multiline)
  const out4a = out.replace(/\b([A-Za-z0-9_:-]+)\(\s*(?!["'\[<\(])([\s\S]*?)\)/g, (_m, id, label) => {
    const t = String(label).trim();
    if (!t) return `${id}(${label})`;
    if (t.startsWith('"') || t.startsWith("'")) return `${id}(${label})`;
    if (/[()：:\[\{]/.test(t)) {
      changed = true;
      return `${id}("${label}")`;
    }
    return `${id}(${label})`;
  });
  if (out4a !== out) changed = true;
  out = out4a;

  // 7) Quote subgraph titles when contain parentheses/colon and not already quoted/id[label]
  const out5 = out.replace(/^(\s*subgraph\s+)([^\n]+)$/gm, (full, pre, name) => {
    const trimmed = String(name).trim();
    if (!trimmed) return full;
    if (trimmed.startsWith('"') || trimmed.startsWith("'")) return full;
    if (trimmed.includes('[')) return full;
    if (/[()：:]/.test(trimmed)) return `${pre}"${trimmed}"`;
    return full;
  });
  if (out5 !== out) changed = true;
  out = out5;

  // 8) If graph has <5 nodes, prefer LR over TD
  try {
    const nodeCount = (() => {
      const ids = new Set();
      // Node declarations: id[...], id{...}, id(...)
      for (const m of out.matchAll(/\b([A-Za-z0-9_:-]+)\s*(?=\[|\{|\()/g)) ids.add(m[1]);
      // Edge endpoints: A --> B, A -.|label|.-> B, A ==>|label| B
      for (const m of out.matchAll(/\b([A-Za-z0-9_:-]+)\s*(?:-->|==>|-\.|-\.)\s*(?:\|[^|]*\|\s*)?\b([A-Za-z0-9_:-]+)/g)) {
        ids.add(m[1]);
        ids.add(m[2]);
      }
      return ids.size;
    })();
    if (nodeCount > 0 && nodeCount < 5) {
      const replaced = out.replace(/^(\s*graph\s+)(TD)\b(.*)$/m, (full, pre, dir, rest) => `${pre}LR${rest}`);
      if (replaced !== out) {
        out = replaced;
        changed = true;
      }
    }
  } catch {}

  return { text: out, changed };
}

function* iterFences(content) {
  const re = /```(mermaid|mermai)\n([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(content)) !== null) {
    yield { lang: m[1], inner: m[2], start: m.index, end: re.lastIndex };
  }
}

async function fixFile(filepath, backupRoot) {
  const original = await fs.readFile(filepath, 'utf8');
  let content = original;
  let changed = false;
  let fixes = 0;

  // Fix misspelled fences globally
  const misspellFixed = content.replace(/```mermai\b/g, '```mermaid');
  if (misspellFixed !== content) {
    content = misspellFixed;
    changed = true;
  }

  // Process each mermaid fence
  const pieces = [];
  let lastIndex = 0;
  for (const f of iterFences(content)) {
    // Push preceding text
    pieces.push(content.slice(lastIndex, f.start));
    lastIndex = f.end;
    const fenceHead = '```mermaid\n';
    const fenceTail = '```';
    const { text: fixed, changed: c } = normalizeMermaid(f.inner);
    fixes += c ? 1 : 0;
    pieces.push(fenceHead + fixed + fenceTail);
  }
  pieces.push(content.slice(lastIndex));
  const newContent = pieces.join('');
  if (newContent !== original) {
    changed = true;
    // Write backup
    const rel = path.relative(await resolveContentRoot(), filepath);
    const backupPath = path.join(backupRoot, rel);
    await fs.mkdir(path.dirname(backupPath), { recursive: true });
    await fs.writeFile(backupPath, original, 'utf8');
    await fs.writeFile(filepath, newContent, 'utf8');
  }
  return { changed, fixes };
}

async function main() {
  const ROOT = await resolveContentRoot();
  const files = await walk(ROOT);
  const backupRoot = path.resolve(process.cwd(), 'output', 'mermaid-backup');
  await fs.mkdir(backupRoot, { recursive: true });

  let changedCount = 0;
  let fixedBlocks = 0;
  for (const file of files) {
    const { changed, fixes } = await fixFile(file, backupRoot);
    if (changed) changedCount++;
    fixedBlocks += fixes;
  }
  console.log(`Mermaid auto-fix completed. Files changed: ${changedCount}, blocks fixed: ${fixedBlocks}`);
  console.log(`Backup originals saved to ${path.relative(process.cwd(), backupRoot)}`);
}

main().catch((e) => {
  console.error('Mermaid auto-fix failed:', e);
  process.exit(1);
});

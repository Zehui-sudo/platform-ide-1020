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

const MERMAID_FENCE = /```mermaid\n([\s\S]*?)```/g;
const MERMAI_MISSPELL = /```mermai\b/g;

/**
 * Heuristic lint rules aligned with our runtime normalizer
 */
function lintBlock(src) {
  const issues = [];
  const lines = src.split(/\r?\n/);
  // Collect nodes for small-graph orientation heuristic
  const nodeIds = new Set();
  // Capture node declarations like: id[...], id{...}, id(...)
  const declRe = /\b([A-Za-z0-9_:-]+)\s*(?=\[|\{|\()/g;
  // Capture edge endpoints in forms like: A --> B, A -.|label|.-> B, A ==>|label| B
  const edgeRe = /\b([A-Za-z0-9_:-]+)\s*(?:-->|==>|-\.|-\.)\s*(?:\|[^|]*\|\s*)?\b([A-Za-z0-9_:-]+)/g;
  // Detect sequence diagram
  const isSequence = /^\s*sequenceDiagram\b/m.test(src);
  lines.forEach((line, idx) => {
    if (/;\s*$/.test(line)) issues.push({ rule: 'TRAILING_SEMICOLON', line: idx + 1, msg: 'Line ends with ;' });
    if (/--\s*["'][^"']+["']\s*-->/.test(line)) issues.push({ rule: 'QUOTED_EDGE_LABEL', line: idx + 1, msg: 'Use -->|label| instead of -- "label" -->' });
    if (/-\.\s*["'][^"']+["']\s*\.->/.test(line)) issues.push({ rule: 'QUOTED_DOTTED_LABEL', line: idx + 1, msg: 'Use -.|label|.-> instead of -. "label" .->' });
    if (/==\s*["'][^"']+["']\s*==>/.test(line)) issues.push({ rule: 'QUOTED_THICK_LABEL', line: idx + 1, msg: 'Use ==>|label| instead of == "label" ==>' });
    if (/\b[A-Za-z0-9_:-]+\[(?!["'])[^\]]*[()：:\[\{]\]/.test(line)) issues.push({ rule: 'UNQUOTED_NODE_LABEL', line: idx + 1, msg: 'Node label with ()/:[{ should be quoted: ["..."]' });
    if (/\b[A-Za-z0-9_:-]+\{(?!["'])[^}]*[()：:\[\{]\}/.test(line)) issues.push({ rule: 'UNQUOTED_NODE_LABEL', line: idx + 1, msg: 'Node label with ()/:[{ should be quoted: {"..."}' });
    if (/^\s*subgraph\s+[^\["']*?[()：:][^\n]*$/.test(line)) issues.push({ rule: 'UNQUOTED_SUBGRAPH_TITLE', line: idx + 1, msg: 'Subgraph title with ()/: should be quoted' });

    // Pipe edge labels containing ()/: should be quoted inside pipes
    const edgePipeRe = /(-->|-\.|==>)\|([^|]*?)\|/g;
    let m;
    while ((m = edgePipeRe.exec(line)) !== null) {
      const label = String(m[2]).trim();
      if (!label) continue;
      if (!label.startsWith('"') && !label.startsWith("'") && /[()：:]/.test(label)) {
        issues.push({ rule: 'UNQUOTED_EDGE_PIPE_LABEL', line: idx + 1, msg: 'Edge label with ()/: should be quoted inside pipes: -->|"..."|' });
      }
    }

    // HTML <br> tags are disallowed in sequenceDiagram text; prefer newlines
    if (/<br\s*\/?\s*>/i.test(line)) {
      if (isSequence) {
        issues.push({ rule: 'SEQDIAG_HTML_BR', line: idx + 1, msg: 'Sequence diagram text should not use <br/>; replace with \\n' });
      } else {
        issues.push({ rule: 'HTML_BR_IN_LABEL', line: idx + 1, msg: 'Avoid HTML <br/> in labels; use plain newlines' });
      }
    }

    // Track node declarations on this line
    let n;
    while ((n = declRe.exec(line)) !== null) nodeIds.add(n[1]);
    // Track edge endpoints on this line
    while ((n = edgeRe.exec(line)) !== null) {
      nodeIds.add(n[1]);
      nodeIds.add(n[2]);
    }
  });

  // Cross-line check: round nodes id(...) whose label contains ()/:[{ and is unquoted
  try {
    const parenNodeRe = /\b([A-Za-z0-9_:-]+)\(\s*([\s\S]*?)\)/g;
    let pm;
    while ((pm = parenNodeRe.exec(src)) !== null) {
      const label = String(pm[2]);
      const trimmed = label.trim();
      if (!trimmed) continue;
      // Skip shapes like id((circle)) or id([stadium]) or labels already quoted
      const afterOpen = src.slice(pm.index).match(/\(([^\s\S])/); // not reliable; fallback to trimmed
      if (trimmed.startsWith('(') || trimmed.startsWith('[') || trimmed.startsWith('<')) continue;
      if (trimmed.startsWith('"') || trimmed.startsWith("'")) continue;
      if (/[()：:\[\{]/.test(trimmed)) {
        const before = src.slice(0, pm.index);
        const lineNo = (before.match(/\n/g) || []).length + 1;
        issues.push({ rule: 'UNQUOTED_NODE_LABEL', line: lineNo, msg: 'Node label with ()/:[{ should be quoted: ("...")' });
      }
    }
  } catch {}

  // Orientation suggestion for small graphs
  const headerMatch = src.match(/^\s*graph\s+([A-Za-z]{2})\b/m);
  if (headerMatch && headerMatch[1] === 'TD') {
    const count = nodeIds.size;
    if (count > 0 && count < 5) {
      issues.push({ rule: 'PREFER_LR_FOR_SMALL_GRAPH', line: 1, msg: `Graph has ${count} nodes; prefer 'graph LR' for clarity` });
    }
  }
  return issues;
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

async function main() {
  const ROOT = await resolveContentRoot();
  const files = await walk(ROOT);
  const report = [];
  for (const file of files) {
    const content = await fs.readFile(file, 'utf8');
    if (MERMAI_MISSPELL.test(content)) {
      const count = (content.match(MERMAI_MISSPELL) || []).length;
      report.push({ file, issue: { rule: 'MISSPELLED_LANGUAGE', line: null, msg: `Found ${count} \`\`\`mermai fences` } });
    }
    let m;
    let index = 0;
    while ((m = MERMAID_FENCE.exec(content)) !== null) {
      index += 1;
      const block = m[1];
      const issues = lintBlock(block);
      for (const issue of issues) {
        report.push({ file, blockIndex: index, issue });
      }
    }
  }

  // Output
  if (report.length === 0) {
    console.log('Mermaid lint: no issues found.');
    return;
  }
  console.log(`Mermaid lint: found ${report.length} issues.\n`);
  for (const r of report) {
    const loc = r.issue.line ? `:${r.issue.line}` : '';
    const bi = r.blockIndex ? ` (block #${r.blockIndex})` : '';
    console.log(`${r.issue.rule} ${r.file}${loc}${bi} - ${r.issue.msg}`);
  }
  // Save JSON report
  const outDir = path.resolve(process.cwd(), 'output');
  try { await fs.mkdir(outDir, { recursive: true }); } catch {}
  const out = path.join(outDir, 'mermaid-lint-report.json');
  await fs.writeFile(out, JSON.stringify(report, null, 2), 'utf8');
  console.log(`\nDetailed report written to ${path.relative(process.cwd(), out)}`);
}

main().catch((e) => {
  console.error('Mermaid lint failed:', e);
  process.exit(1);
});

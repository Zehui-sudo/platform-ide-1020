#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const publicDir = path.join(projectRoot, 'public');
const fontsRoot = path.join(publicDir, 'fonts');
const outJson = path.join(publicDir, 'learn-fonts.json');
const outCss = path.join(publicDir, 'learn-fonts.css');

/**
 * Convert kebab/snake/camel to Title Case words.
 */
function toTitleCase(input) {
  if (!input) return '';
  const withSpaces = input
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2');
  return withSpaces
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
    .trim();
}

function readIfExists(file) {
  try {
    if (fs.existsSync(file)) {
      return fs.readFileSync(file, 'utf8');
    }
  } catch {}
  return null;
}

function formatFamilyList(ff) {
  if (!ff) return '';
  const raw = ff.trim();
  // If already a comma-separated list, return as-is (each segment may include spaces)
  if (raw.includes(',')) return raw;
  // Quote single family with spaces
  if (/\s/.test(raw)) return `'${raw}'`;
  return raw;
}

function discoverFonts() {
  const items = [];
  if (!fs.existsSync(fontsRoot)) return items;
  const entries = fs.readdirSync(fontsRoot, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const id = e.name;
    if (id.startsWith('.')) continue;
    const dir = path.join(fontsRoot, id);

    let displayName = null;
    let fontFamily = null;
    let css = '';

    // meta.json (optional)
    const metaPath = path.join(dir, 'meta.json');
    let hasMeta = false;
    try {
      if (fs.existsSync(metaPath)) {
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        if (typeof meta.displayNameCN === 'string' && meta.displayNameCN.trim()) {
          displayName = meta.displayNameCN.trim();
        }
        if (typeof meta.fontFamily === 'string' && meta.fontFamily.trim()) {
          fontFamily = meta.fontFamily.trim();
        }
        hasMeta = true;
      }
    } catch {}

    // font.css (optional)
    const cssPath = path.join(dir, 'font.css');
    const cssContent = readIfExists(cssPath);
    const hasCss = !!cssContent;
    if (cssContent) {
      css += `\n/* ${id} font.css */\n` + cssContent + '\n';
      if (!fontFamily) {
        const m = cssContent.match(/font-family\s*:\s*['\"]?([^'\";]+)['\"]?\s*;/i);
        if (m) fontFamily = m[1].trim();
      }
    }

    // Collect woff2 files once for decisions below
    let woff2Files = [];
    try {
      woff2Files = fs.readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.woff2'));
    } catch {}

    // If directory has no meta, no css, and no woff2, skip it from manifest
    if (!hasMeta && !hasCss && woff2Files.length === 0) {
      continue;
    }

    // If no font.css, auto-generate @font-face from all .woff2 with heuristics
    if (!cssContent) {
      const files = woff2Files;
      if (files.length > 0) {
        if (!fontFamily) fontFamily = toTitleCase(id);

        const guessWeight = (name) => {
          const n = name.toLowerCase();
          // Named weights
          if (/(thin)/.test(n)) return 100;
          if (/(extra[-_\s]?light|ultra[-_\s]?light)/.test(n)) return 200;
          if (/(light)/.test(n)) return 300;
          if (/(book)/.test(n)) return 400;
          if (/(regular|normal)/.test(n)) return 400;
          if (/(medium)/.test(n)) return 500;
          if (/(semi[-_\s]?bold|demi[-_\s]?bold)/.test(n)) return 600;
          if (/(bold)/.test(n)) return 700;
          if (/(extra[-_\s]?bold|ultra[-_\s]?bold)/.test(n)) return 800;
          if (/(black|heavy)/.test(n)) return 900;
          // Numeric 100..900
          const m100 = n.match(/(?:^|[-_])(100|200|300|400|500|600|700|800|900)(?:[-_.]|$)/);
          if (m100) return parseInt(m100[1], 10);
          // Alibaba 55/65/75/85 style or similar 2-digit clues
          const m2 = n.match(/(?:^|[-_])(\d{2})(?:[-_.]|$)/);
          if (m2) {
            const v = parseInt(m2[1], 10);
            if (v <= 35) return 200;
            if (v <= 45) return 300;
            if (v <= 60) return 400;
            if (v <= 70) return 500;
            if (v <= 80) return 600;
            if (v <= 90) return 700;
            return 900;
          }
          return 400;
        };

        const guessStyle = (name) => {
          const n = name.toLowerCase();
          if (/(italic)/.test(n)) return 'italic';
          if (/(oblique)/.test(n)) return 'oblique';
          return 'normal';
        };

        const isVariable = (name) => /variable|var/gi.test(name);

        files.sort();
        css += `\n/* ${id} auto-generated */\n`;
        for (const f of files) {
          const urlPath = `/fonts/${id}/${f}`;
          const weight = isVariable(f) && files.length === 1 ? '100 900' : String(guessWeight(f));
          const style = guessStyle(f);
          css += `@font-face {\n  font-family: '${fontFamily}';\n  src: url('${urlPath}') format('woff2');\n  font-weight: ${weight};\n  font-style: ${style};\n  font-display: swap;\n}\n\n`;
        }
      }
    }

    if (!fontFamily) fontFamily = toTitleCase(id);
    if (!displayName) displayName = fontFamily;

    // Helper class for optional use
    css += `\n/* helper class */\n.app-font-${id} {\n  font-family: ${formatFamilyList(fontFamily)}, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', PingFang SC, 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans CJK SC', 'Helvetica Neue', Arial, sans-serif;\n}\n`;

    items.push({ id, displayName, fontFamily, css });
  }
  return items;
}

function main() {
  try {
    const fonts = discoverFonts();
    // Write JSON manifest
    const manifest = fonts.map(({ id, displayName, fontFamily }) => ({ id, displayName, fontFamily }));
    fs.writeFileSync(outJson, JSON.stringify(manifest, null, 2), 'utf8');
    // Write CSS bundle
    const banner = `/* learn-fonts.css generated: ${new Date().toISOString()} */\n`;
    const css = banner + fonts.map((f) => f.css).join('\n');
    fs.writeFileSync(outCss, css, 'utf8');
    console.log(`Generated ${path.relative(projectRoot, outJson)} and ${path.relative(projectRoot, outCss)} with ${fonts.length} font(s).`);
  } catch (e) {
    console.error('Failed to generate font manifest:', e);
    try {
      fs.writeFileSync(outJson, '[]', 'utf8');
      fs.writeFileSync(outCss, '/* failed to generate fonts */\n', 'utf8');
    } catch {}
    process.exitCode = 1;
  }
}

main();

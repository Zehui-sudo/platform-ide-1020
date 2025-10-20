#!/usr/bin/env node
 
const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const https = require('https');

const ROOT = path.resolve(__dirname, '..');
const TARGET_DIR = path.join(ROOT, 'resources', 'wasm');

const GRAMMARS = ['javascript', 'typescript', 'tsx', 'python', 'java', 'go', 'rust'];

const DOWNLOAD_SOURCES = {
  javascript: [
    'https://unpkg.com/tree-sitter-javascript/tree-sitter-javascript.wasm',
  ],
  typescript: [
    'https://github.com/tree-sitter/tree-sitter-typescript/releases/latest/download/tree-sitter-typescript.wasm',
  ],
  tsx: [
    'https://github.com/tree-sitter/tree-sitter-typescript/releases/latest/download/tree-sitter-tsx.wasm',
  ],
  python: [
    'https://unpkg.com/tree-sitter-python/tree-sitter-python.wasm',
  ],
  java: [
    'https://unpkg.com/tree-sitter-java/tree-sitter-java.wasm',
  ],
  go: [
    'https://unpkg.com/tree-sitter-go/tree-sitter-go.wasm',
  ],
  rust: [
    'https://unpkg.com/tree-sitter-rust/tree-sitter-rust.wasm',
  ],
};

async function ensureDir(dir) {
  await fsp.mkdir(dir, { recursive: true }).catch(() => {});
}

function exists(p) {
  try {
    fs.accessSync(p, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function resolveRuntimeWasm() {
  try {
    return require.resolve('web-tree-sitter/tree-sitter.wasm');
  } catch {}
  try {
    const main = require.resolve('web-tree-sitter');
    const dir = path.dirname(main);
    const candidates = [
      path.join(dir, 'tree-sitter.wasm'),
      path.join(dir, 'lib', 'tree-sitter.wasm'),
      path.join(dir, 'debug', 'tree-sitter.wasm'),
    ];
    for (const c of candidates) {
      if (exists(c)) return c;
    }
  } catch {}
  return null;
}

async function copyFileSafe(src, dest) {
  if (!src) return false;
  try {
    await ensureDir(path.dirname(dest));
    await fsp.copyFile(src, dest);
    console.log(`Copied: ${path.relative(ROOT, dest)}`);
    return true;
  } catch (e) {
    console.warn(`Failed to copy ${src} -> ${dest}:`, e.message);
    return false;
  }
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https
      .get(url, (res) => {
        if (res.statusCode && res.statusCode >= 400) {
          file.close();
          fs.unlink(dest, () => {});
          return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        }
        res.pipe(file);
        file.on('finish', () => file.close(() => resolve(true)));
      })
      .on('error', (err) => {
        file.close();
        fs.unlink(dest, () => {});
        reject(err);
      });
  });
}

async function maybeDownloadGrammar(lang) {
  const file = `tree-sitter-${lang}.wasm`;
  const dest = path.join(TARGET_DIR, file);
  if (exists(dest)) return true;

  const sourceDir = process.env.LEARN_LINKER_WASM_SOURCE;
  if (sourceDir) {
    const src = path.join(sourceDir, file);
    if (exists(src)) return copyFileSafe(src, dest);
  }

  if (!process.argv.includes('--download')) return false;

  const urls = DOWNLOAD_SOURCES[lang] || [];
  for (const url of urls) {
    try {
      await ensureDir(TARGET_DIR);
      await download(url, dest);
      console.log(`Downloaded ${file} from ${url}`);
      return true;
    } catch (e) {
      console.warn(`Could not download ${file} from ${url}: ${e.message}`);
    }
  }
  return false;
}

async function main() {
  await ensureDir(TARGET_DIR);

  // Copy runtime wasm
  const runtimeSrc = resolveRuntimeWasm();
  const runtimeDest = path.join(TARGET_DIR, 'tree-sitter.wasm');
  if (!exists(runtimeDest)) {
    if (!runtimeSrc) {
      console.warn('Runtime tree-sitter.wasm not found in node_modules.');
    } else {
      await copyFileSafe(runtimeSrc, runtimeDest);
    }
  }

  // Copy or download grammars when available
  const only = (process.argv.find((a) => a.startsWith('--langs=')) || '').split('=')[1];
  const langs = only ? only.split(',').map((s) => s.trim()).filter(Boolean) : GRAMMARS;

  for (const lang of langs) {
    const ok = await maybeDownloadGrammar(lang);
    if (!ok) {
      const fname = `tree-sitter-${lang}.wasm`;
      if (!exists(path.join(TARGET_DIR, fname))) {
        console.log(`Grammar ${fname} not found. Place it under resources/wasm to enable ${lang}.`);
      }
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});

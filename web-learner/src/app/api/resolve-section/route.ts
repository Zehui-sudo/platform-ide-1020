import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

function sanitizeLang(input: string): string | null {
  // Allow only simple folder names (letters, numbers, dash, underscore)
  if (!/^[A-Za-z0-9_-]+$/.test(input)) return null;
  return input;
}

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const langParam = url.searchParams.get('subject') || url.searchParams.get('lang') || '';
    const idParam = url.searchParams.get('id') || '';

    const lang = sanitizeLang(langParam || '');
    const id = (idParam || '').trim();

    if (!lang || !id) {
      return NextResponse.json({ error: 'Missing lang or id' }, { status: 400 });
    }

    const publicDir = path.join(process.cwd(), 'public');
    const contentDir = path.join(publicDir, 'content', lang);

    if (!fs.existsSync(contentDir) || !fs.statSync(contentDir).isDirectory()) {
      return NextResponse.json({ error: 'Language content directory not found' }, { status: 404 });
    }

    const entries = fs.readdirSync(contentDir, { withFileTypes: true });
    const mdFiles = entries
      .filter((e) => e.isFile() && e.name.toLowerCase().endsWith('.md'))
      .map((e) => e.name);

    const lowerId = id.toLowerCase();

    // Prefer exact match first
    const exact = mdFiles.find((f) => f.replace(/\.md$/i, '').toLowerCase() === lowerId);
    if (exact) {
      return NextResponse.json({ path: `/content/${lang}/${exact}` });
    }

    // Then prefix match: id****.md (allow any suffix after id)
    const prefixMatches = mdFiles.filter((f) => f.replace(/\.md$/i, '').toLowerCase().startsWith(lowerId));
    if (prefixMatches.length > 0) {
      // Deterministic selection: shortest name first, then lexicographical
      const best = prefixMatches.sort((a, b) => {
        if (a.length !== b.length) return a.length - b.length;
        return a.localeCompare(b, 'en');
      })[0];
      return NextResponse.json({ path: `/content/${lang}/${best}` });
    }

    return NextResponse.json({ error: 'Section markdown not found' }, { status: 404 });
  } catch (_e) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}

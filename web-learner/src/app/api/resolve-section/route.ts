import { NextResponse } from 'next/server';
import { promises as fsp } from 'node:fs';
import path from 'node:path';

export const runtime = 'nodejs';

const PROJECT_ROOT = process.cwd();
const CONTENT_ROOT = path.join(PROJECT_ROOT, 'public', 'content');

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const subject = searchParams.get('subject')?.trim();
  const sectionId = searchParams.get('id')?.trim();

  if (!subject || !sectionId) {
    return NextResponse.json(
      { error: 'subject and id are required' },
      { status: 400 },
    );
  }

  const subjectDir = path.join(CONTENT_ROOT, subject);

  try {
    const files = await fsp.readdir(subjectDir);
    const candidates = files.filter(
      (file) =>
        file.endsWith('.md') &&
        file.toLowerCase().includes(sectionId.toLowerCase()),
    );
    if (candidates.length === 0) {
      return NextResponse.json({ error: 'not found' }, { status: 404 });
    }
    const filename = candidates[0];
    const resolved = path.join('/content', subject, filename);
    const fullPath = path.join(subjectDir, filename);
    const markdown = await fsp.readFile(fullPath, 'utf8');

    return NextResponse.json(
      { path: resolved, markdown },
      {
        headers: {
          'Cache-Control': 'no-store',
        },
      },
    );
  } catch (error: unknown) {
    const code = (error as NodeJS.ErrnoException)?.code;
    if (code === 'ENOENT') {
      return NextResponse.json({ error: 'subject not found' }, { status: 404 });
    }
    console.error('[api/resolve-section] failed', { subject, sectionId, error });
    return NextResponse.json(
      { error: 'failed to resolve section' },
      { status: 500 },
    );
  }
}

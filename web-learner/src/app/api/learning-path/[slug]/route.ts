import { NextResponse } from 'next/server';
import { promises as fsp } from 'node:fs';
import path from 'node:path';

export const runtime = 'nodejs';

const PROJECT_ROOT = process.cwd();
const LEARN_DATA_DIR = path.join(PROJECT_ROOT, 'public', 'learn-data');

export async function GET(
  _request: Request,
  { params }: { params: { slug: string } },
) {
  const slug = params.slug?.trim();
  if (!slug) {
    return NextResponse.json({ error: 'slug is required' }, { status: 400 });
  }

  const filePath = path.join(LEARN_DATA_DIR, `${slug}.json`);

  try {
    const raw = await fsp.readFile(filePath, 'utf8');
    const json = JSON.parse(raw);
    return NextResponse.json(json, {
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  } catch (error: unknown) {
    const code = (error as NodeJS.ErrnoException)?.code;
    if (code === 'ENOENT') {
      return NextResponse.json({ error: 'not found' }, { status: 404 });
    }
    console.error('[api/learning-path] 读取失败', { slug, error });
    return NextResponse.json(
      { error: 'failed to load learning path' },
      { status: 500 },
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { getJob } from '@/server/pipeline/jobManager';
import { startChapters } from '@/server/pipeline/spawnChapters';

export const runtime = 'nodejs';

function repoRoot(): string {
  return path.resolve(process.cwd(), '..');
}

const toErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    console.log('[pipeline] /api/content/start body:', body);
    const refJobId: string | undefined = body?.refJobId ? String(body.refJobId) : undefined;
    let inputPath: string | undefined = body?.inputPath ? String(body.inputPath) : undefined;
    const selectedChapters: string | undefined = body?.selectedChapters ? String(body.selectedChapters) : undefined;
    // 默认开启 debug，确保脚本按自身机制记录日志到 output/<slug>/log.txt
    const debug: boolean = Boolean(body?.debug ?? true);

    if (!inputPath && refJobId) {
      const ref = getJob(refJobId);
      if (ref?.outputPath && ref.status === 'success') {
        inputPath = ref.outputPath;
      }
    }

    if (!inputPath) {
      return NextResponse.json({ error: '缺少 inputPath 或 refJobId' }, { status: 400 });
    }

    // 允许相对路径（相对于仓库根）或绝对路径
    if (!path.isAbsolute(inputPath)) {
      inputPath = path.join(repoRoot(), inputPath);
    }
    try {
      const st = await fs.stat(inputPath);
      if (!st.isFile()) throw new Error('not a file');
    } catch {
      return NextResponse.json({ error: `找不到集成大纲文件: ${inputPath}` }, { status: 400 });
    }

    const job = await startChapters({ inputPath, selectedChapters, debug });
    return NextResponse.json({ jobId: job.id });
  } catch (error: unknown) {
    return NextResponse.json({ error: toErrorMessage(error) }, { status: 500 });
  }
}

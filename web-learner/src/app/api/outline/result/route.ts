import { NextRequest, NextResponse } from 'next/server';
import { getJob } from '@/server/pipeline/jobManager';
import fs from 'fs/promises';

export const runtime = 'nodejs';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const jobId = searchParams.get('jobId') || '';
    const job = jobId ? getJob(jobId) : undefined;
    if (!job) return new Response('job not found', { status: 404 });
    if (!job.outputPath) return NextResponse.json({ error: '输出文件尚未确定', status: job.status }, { status: 202 });

    const text = await fs.readFile(job.outputPath, { encoding: 'utf-8' });
    const json = JSON.parse(text);
    return NextResponse.json(json);
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
  }
}

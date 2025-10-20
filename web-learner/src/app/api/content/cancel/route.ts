import { NextRequest, NextResponse } from 'next/server';
import { broadcast, finishJob, getJob, updateStage } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  try {
    let jobId: string | undefined;
    try {
      const body = await req.json();
      jobId = body?.jobId ? String(body.jobId) : undefined;
    } catch {}
    if (!jobId) {
      const { searchParams } = new URL(req.url);
      jobId = searchParams.get('jobId') || '';
    }
    if (!jobId) return NextResponse.json({ error: 'missing jobId' }, { status: 400 });

    const job = getJob(jobId);
    if (!job) return NextResponse.json({ error: `job not found: ${jobId}` }, { status: 404 });

    let killed = false;
    try {
      if (typeof job.pid === 'number' && job.pid > 0) {
        process.kill(job.pid, 'SIGTERM');
        killed = true;
      }
    } catch (e) {
      // ignore
    }

    finishJob(job.id, 'cancelled');
    updateStage(job, 'content', { status: 'error', detail: '已取消' });
    broadcast(job, 'log', { line: `[orchestrator] cancelled by user` });
    broadcast(job, 'end', { status: 'cancelled' });

    return NextResponse.json({ ok: true, killed });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
  }
}


import { NextRequest, NextResponse } from 'next/server';
import { getJob, finishJob, broadcast } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const jobId = searchParams.get('jobId') || '';
    const job = jobId ? getJob(jobId) : undefined;
    if (!job) return NextResponse.json({ error: 'job not found' }, { status: 404 });

    try {
      if (job.pid) {
        try { process.kill(job.pid, 'SIGTERM'); } catch {}
      }
      finishJob(job.id, 'cancelled');
      broadcast(job, 'end', { status: 'cancelled' });
    } catch (e: any) {
      return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || String(e) }, { status: 500 });
  }
}


import { NextRequest, NextResponse } from 'next/server';
import { getJob, finishJob, broadcast } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

const toErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

export async function POST(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const jobId = searchParams.get('jobId') || '';
    const job = jobId ? getJob(jobId) : undefined;
    if (!job) return NextResponse.json({ error: 'job not found' }, { status: 404 });

    try {
      if (job.pid) {
        try {
          process.kill(job.pid, 'SIGTERM');
        } catch {
          // Ignore process termination failures; process may already be gone.
        }
      }
      finishJob(job.id, 'cancelled');
      broadcast(job, 'end', { status: 'cancelled' });
    } catch (innerError: unknown) {
      return NextResponse.json({ error: toErrorMessage(innerError) }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch (error: unknown) {
    return NextResponse.json({ error: toErrorMessage(error) }, { status: 500 });
  }
}

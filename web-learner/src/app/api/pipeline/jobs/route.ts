import { NextResponse } from 'next/server';
import { listJobs, snapshot } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

export async function GET() {
  try {
    const jobs = listJobs()
      .map((job) => snapshot(job))
      .sort((a, b) => b.startTs - a.startTs);
    return NextResponse.json({ jobs });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

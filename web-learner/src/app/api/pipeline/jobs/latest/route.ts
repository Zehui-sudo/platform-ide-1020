import { NextRequest, NextResponse } from 'next/server';
import { latestJob, snapshot } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const type = searchParams.get('type');
    if (type !== 'outline' && type !== 'content') {
      return NextResponse.json({ error: 'invalid type' }, { status: 400 });
    }
    const job = latestJob(type);
    if (!job) {
      return NextResponse.json({ job: null });
    }
    return NextResponse.json({ job: snapshot(job) });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

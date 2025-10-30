import { NextRequest, NextResponse } from 'next/server';
import { getJob, snapshot } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

interface RouteParams {
  params: { id: string };
}

export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const id = params.id;
    if (!id) {
      return NextResponse.json({ error: 'missing id' }, { status: 400 });
    }
    const job = getJob(id);
    if (!job) {
      return NextResponse.json({ error: 'job not found' }, { status: 404 });
    }
    return NextResponse.json({ job: snapshot(job) });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

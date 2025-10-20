import { NextRequest } from 'next/server';
import { attachSSE, getJob, snapshot } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const jobId = searchParams.get('jobId') || '';
  const job = jobId ? getJob(jobId) : undefined;
  if (!job) {
    return new Response(`job not found: ${jobId}`, { status: 404 });
  }

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const client = attachSSE(job, controller);
      client.send('hello', { jobId, snapshot: snapshot(job) });
      for (const st of Object.values(job.stages)) client.send('stage', st);
      const t = setInterval(() => {
        try { controller.enqueue(new TextEncoder().encode(`: ping\n\n`)); } catch {}
      }, 20000);
      const close = () => { clearInterval(t); try { controller.close(); } catch {} };
      if (job.status !== 'running') {
        client.send('end', { status: job.status, outputPath: job.outputPath, logPath: job.logPath });
        close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}


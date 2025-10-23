import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';
import { getJob } from '@/server/pipeline/jobManager';

export const runtime = 'nodejs';

function repoRoot(): string {
  return path.resolve(process.cwd(), '..');
}

function tryInferSlugFromReport(p?: string): string | undefined {
  if (!p) return undefined;
  const base = path.basename(p);
  const m = base.match(/^pipeline_report_(.+)\.md$/);
  return m?.[1];
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const jobId = searchParams.get('jobId') || '';
    const job = jobId ? getJob(jobId) : undefined;
    if (!job) return new Response('job not found', { status: 404 });

    const reportPath = job.outputPath;
    const slug = tryInferSlugFromReport(reportPath);
    const publishDir = slug ? path.join(repoRoot(), 'web-learner', 'public', 'content', slug) : undefined;
    let publishedFiles: string[] | undefined;
    if (publishDir) {
      try {
        const ents = await fs.readdir(publishDir, { withFileTypes: true });
        publishedFiles = ents
          .filter(e => e.isFile() && e.name.toLowerCase().endsWith('.md'))
          .map(e => path.join('web-learner', 'public', 'content', slug!, e.name));
      } catch {}
    }

    return NextResponse.json({
      subject: job.subject,
      reportPath: reportPath && (path.isAbsolute(reportPath) ? reportPath : path.join(repoRoot(), reportPath)),
      logPath: job.logPath,
      publishDir,
      publishedFiles,
      status: job.status,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { startIntegrated } from '@/server/pipeline/spawnIntegrated';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const subject = String(body?.subject || '').trim();
    const learningStyle = String(body?.learningStyle || '').trim().toLowerCase();
    const expectedContent = String(body?.expectedContent || '').trim();
    const topN = body?.topN != null ? Number(body.topN) : undefined;
    const printPrompt = Boolean(body?.printPrompt ?? true);
    const debug = Boolean(body?.debug ?? false);

    if (!subject) {
      return NextResponse.json({ error: '主题 subject 必填' }, { status: 400 });
    }
    const styleMap: Record<string, 'principles'|'deep_preview'> = {
      principles: 'principles', '原理学习': 'principles',
      deep_preview: 'deep_preview', '深度预习': 'deep_preview',
    };
    const style = styleMap[learningStyle];
    if (!style) {
      return NextResponse.json({ error: '学习风格必须为 principles/deep_preview（或中文）' }, { status: 400 });
    }

    const job = startIntegrated({
      subject,
      learningStyle: style,
      expectedContent: expectedContent || undefined,
      topN,
      printPrompt,
      debug,
    });
    return NextResponse.json({ jobId: job.id });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import { broadcast, createJob, finishJob, JobRecord, touchJob, updateStage } from './jobManager';

export interface GenerateContentParams {
  inputPath: string; // integrated JSON path
  selectedChapters?: string; // e.g., "1,3-4"
  debug?: boolean; // enable script's own debug logging
}

function repoRoot(): string {
  // Next app cwd is web-learner; repoRoot is parent
  return path.resolve(process.cwd(), '..');
}

function slugify(text: string): string {
  const s = (text || '').trim().toLowerCase()
    .replace(/[\u3000\s/]+/g, '-')
    .replace(/[^a-z0-9\-_.]+/g, '')
    .replace(/-+/g, '-').replace(/^-+|-+$/g, '');
  return s || 'topic';
}

async function deriveTopicFromIntegrated(integratedPath: string): Promise<{ subject?: string, topicSlug: string }>
{
  try {
    const text = await fs.readFile(integratedPath, { encoding: 'utf-8' });
    const json = JSON.parse(text);
    const subject: string | undefined = json?.subject || json?.reconstructed_outline?.meta?.subject;
    const topicSlug = (
      (json?.reconstructed_outline?.meta?.topic_slug && String(json.reconstructed_outline.meta.topic_slug)) ||
      (json?.subject_slug && String(json.subject_slug)) ||
      slugify(String(subject || ''))
    );
    return { subject, topicSlug };
  } catch {
    return { subject: undefined, topicSlug: 'topic' };
  }
}

async function computeSectionTotals(integratedPath: string): Promise<{ total: number; perChapter: number[] }> {
  try {
    const text = await fs.readFile(integratedPath, { encoding: 'utf-8' });
    const json = JSON.parse(text);
    const outline = json?.reconstructed_outline || json;
    let total = 0;
    const perChapter: number[] = [];
    if (Array.isArray(outline?.groups)) {
      for (const g of outline.groups) {
        const c = Array.isArray(g?.sections) ? g.sections.length : 0;
        perChapter.push(c);
        total += c;
      }
    } else if (Array.isArray(outline?.chapters)) {
      for (const cpt of outline.chapters) {
        const c = Array.isArray(cpt?.sections) ? cpt.sections.length : 0;
        perChapter.push(c);
        total += c;
      }
    } else if (Array.isArray(outline?.sections)) {
      total = outline.sections.length;
      if (total > 0) perChapter.push(total);
    }
    return { total, perChapter };
  } catch {
    return { total: 0, perChapter: [] };
  }
}

function parseLine(
  job: JobRecord,
  line: string,
  counters: { draft: number; total: number; perChapter: number[]; finalized: boolean; reviewStarted: boolean }
): void {
  try {
    // 选择章节信息
    const mSel = line.match(/选择章节\s*:\s*\[([^\]]*)\]/);
    if (mSel) {
      const list = mSel[1].split(',').map(s => s.trim()).filter(Boolean);
      // 尝试根据选择章节重算总量（章节编号通常为 1-based）
      let selectedTotal = 0;
      for (const tok of list) {
        const n = parseInt(tok, 10);
        if (!isNaN(n) && n > 0 && n <= counters.perChapter.length) {
          selectedTotal += counters.perChapter[n - 1];
        }
      }
      if (selectedTotal > 0) counters.total = selectedTotal;
      const prog = counters.total > 0 ? Math.min(0.9, (counters.draft / counters.total) * 0.9) : undefined;
      updateStage(job, 'content', {
        status: 'running',
        detail: `选择章节: ${list.length} 个（目标 ${counters.total || '?'} 个知识点）`,
        progress: prog,
      });
      return;
    }

    // 初稿保存（占 90%）
    if (/\[已保存初稿\]/.test(line)) {
      counters.draft += 1;
      const base = counters.total > 0 ? `初稿 ${counters.draft}/${counters.total}` : `初稿 ${counters.draft}`;
      const prog = counters.total > 0 ? Math.min(0.9, (counters.draft / counters.total) * 0.9) : undefined;
      updateStage(job, 'content', {
        status: 'running',
        detail: base,
        progress: prog,
      });
      return;
    }

    // 审核阶段入口
    if (!counters.reviewStarted && line.includes('==== LLM Prompt [propose_fix] BEGIN ====')) {
      counters.reviewStarted = true;
      const reviewDetail = counters.total > 0
        ? `初稿 ${counters.draft}/${counters.total} · 审核阶段`
        : '审核阶段：模型输出质检中…';
      updateStage(job, 'content', {
        status: 'running',
        detail: reviewDetail,
        progress: counters.total > 0 ? Math.max(0.9, Math.min(0.98, counters.draft / counters.total)) : undefined,
      });
      return;
    }

    // 最终落盘（发布完成，+10%）
    if (/\[大纲已保存\]/.test(line) || /大纲已保存\s*:\s*/.test(line)) {
      counters.finalized = true;
      const base = counters.total > 0 ? `初稿 ${counters.draft}/${counters.total} · 已发布` : `已发布`;
      updateStage(job, 'content', {
        status: 'running',
        detail: base,
        progress: 1,
      });
      return;
    }

    // 报告路径（作为输出路径）
    const mReport = line.match(/报告已写出\s*:\s*(.+)$/);
    if (mReport) {
      job.outputPath = mReport[1].trim();
      touchJob(job);
      // 试着推导 log 与发布目录并广播
      try {
        const base = path.basename(job.outputPath || ''); // pipeline_report_<slug>.md
        const m = base.match(/^pipeline_report_(.+)\.md$/);
        if (m) {
          const slug = m[1];
          const publishDir = path.join(repoRoot(), 'web-learner', 'public', 'content', slug);
          // 约定调试日志
          const logPath = path.join(repoRoot(), 'output', slug, 'log.txt');
          job.logPath = logPath;
          touchJob(job);
          broadcast(job, 'file', { reportPath: job.outputPath, publishDir, logPath });
        } else {
          broadcast(job, 'file', { reportPath: job.outputPath });
        }
      } catch {}
      return;
    }

    // 完成标记
    if (/✅\s*完成/.test(line) || /完成。无报告可显示。/.test(line)) {
      updateStage(job, 'content', { status: 'completed', progress: 1, detail: '完成' });
      return;
    }
  } catch {}
}

export async function startChapters(params: GenerateContentParams) {
  const { inputPath } = params;
  console.log('[pipeline] startChapters invoked with params:', params);
  const meta = await deriveTopicFromIntegrated(inputPath);
  const totals = await computeSectionTotals(inputPath);
  const job = createJob('content', {
    subject: meta.subject,
  });
  console.log('[pipeline] startChapters createJob id=', job.id, 'subject=', meta.subject, 'totals=', totals);

  const py = process.env.PYTHON || 'python';
  const script = path.join(repoRoot(), 'scripts', 'pipelines', 'generation', 'generate_chapters_from_integrated_standalone.py');

  const args: string[] = [
    '-u',
    script,
    '--input', inputPath,
    '--config', path.join(repoRoot(), 'config.json'),
  ];
  args.push('--skip-content-review');
  if (params.selectedChapters && params.selectedChapters.trim()) {
    args.push('--selected-chapters', params.selectedChapters.trim());
  }
  if (params.debug || process.env.PIPELINE_LOG === '1') args.push('--debug');

  // 设置脚本内置日志路径（仅在 --debug 时有效）
  const slug = meta.topicSlug || 'topic';
  const dbgLogDir = path.join(repoRoot(), 'output', slug);
  await fs.mkdir(dbgLogDir, { recursive: true }).catch(() => {});
  const dbgLogPath = path.join(dbgLogDir, 'log.txt');
  job.logPath = dbgLogPath;
  touchJob(job);

  const child = spawn(py, args, { cwd: repoRoot(), env: process.env });
  job.pid = child.pid;
  console.log('[pipeline] startChapters spawned process:', { pid: child.pid, args, cwd: repoRoot() });
  touchJob(job);

  // 初始阶段
  updateStage(job, 'content', {
    status: 'running',
    detail: totals.total > 0 ? `初稿 0/${totals.total}` : '启动脚本中…',
    progress: totals.total > 0 ? 0 : undefined,
  });
  broadcast(job, 'log', { line: `[orchestrator] spawn: ${py} ${args.join(' ')}` });
  broadcast(job, 'log', { line: `[orchestrator] cwd: ${repoRoot()}` });
  // 提前广播日志文件位置（脚本内置 log）
  broadcast(job, 'file', { logPath: dbgLogPath });

  child.on('spawn', () => {
    broadcast(job, 'log', { line: `[orchestrator] process started (pid=${child.pid})` });
    updateStage(job, 'content', { status: 'running', detail: '准备生成章节内容' });
  });

  const counters = { draft: 0, total: totals.total, perChapter: totals.perChapter, finalized: false, reviewStarted: false };
  const onData = (buf: Buffer) => {
    const text = buf.toString('utf-8');
    const lines = text.split(/\r?\n/);
    for (const line of lines) {
      if (!line) continue;
      broadcast(job, 'log', { line });
      parseLine(job, line, counters);
    }
  };
  child.stdout.on('data', onData);
  child.stderr.on('data', onData);

  child.on('close', (code) => {
    console.log('[pipeline] content child close event:', { pid: child.pid, code });
    if (code === 0) {
      finishJob(job.id, 'success');
      broadcast(job, 'end', { status: 'success', outputPath: job.outputPath, logPath: job.logPath });
    } else {
      finishJob(job.id, 'error');
      updateStage(job, 'content', { status: 'error', detail: `进程退出码 ${code}` });
      broadcast(job, 'end', { status: 'error', message: `进程退出码 ${code}` });
    }
  });
  child.on('error', (err) => {
    console.log('[pipeline] content child error event:', err);
    finishJob(job.id, 'error');
    updateStage(job, 'content', { status: 'error', detail: '进程启动失败' });
    broadcast(job, 'log', { line: `[orchestrator] spawn error: ${String(err?.message || err)}` });
    broadcast(job, 'end', { status: 'error', message: String(err?.message || err) });
  });

  return job;
}

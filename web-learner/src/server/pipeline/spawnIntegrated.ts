import { spawn } from 'child_process';
import path from 'path';
import { broadcast, createJob, finishJob, JobRecord, updateStage } from './jobManager';

export interface IntegratedParams {
  subject: string;
  learningStyle: 'principles' | 'deep_preview';
  expectedContent?: string;
  topN?: number;
  printPrompt?: boolean;
  debug?: boolean;
  geminiKey?: string; // optional override of config keys
  kimiKey?: string;
}

function repoRoot(): string {
  // Next app cwd is web-learner; repoRoot is parent
  return path.resolve(process.cwd(), '..');
}

function parseLineForStages(job: JobRecord, line: string) {
  try {
    // collect stage start
    if (/\[1\/2\]\s*调用\s*Gemini\s*推荐教材/.test(line)) {
      updateStage(job, 'collect', { status: 'running', detail: '调用 Gemini 推荐经典教材' });
    }
    const mPar = line.match(/并行检索教材目录 .*待检索=(\d+)\s*本/);
    if (mPar) {
      const total = parseInt(mPar[1], 10);
      job.totalToFetch = total;
      job.processed = 0;
      updateStage(job, 'collect', { status: 'running', progress: 0, detail: `已完成 0/${total}` });
    }
    if (/^完成: 《/.test(line) || /^完成但有错误:/.test(line) || /^任务异常:/.test(line)) {
      if (typeof job.processed !== 'number') job.processed = 0;
      job.processed += 1;
      const total = job.totalToFetch || 0;
      const prog = total > 0 ? job.processed / total : undefined;
      updateStage(job, 'collect', { status: 'running', progress: prog, detail: `已完成 ${job.processed}/${total || '?'} ` });
    }
    const mOk = line.match(/目录获取成功:\s*(\d+)\/(\d+)/);
    if (mOk) {
      const ok = parseInt(mOk[1], 10);
      const all = parseInt(mOk[2], 10);
      updateStage(job, 'collect', { status: 'completed', progress: 1, detail: `成功 ${ok}/${all}` });
    }

    // outline stage
    if (/主题分类结果:/.test(line)) {
      updateStage(job, 'outline', { status: 'running', detail: '开始整合生成大纲' });
    }
    if (/正在以流式方式接收模型输出/.test(line)) {
      updateStage(job, 'outline', { status: 'running', detail: '模型输出中…' });
    }
    if (/大纲重构: 成功/.test(line)) {
      updateStage(job, 'outline', { status: 'completed', progress: 1, detail: '完成' });
    }
    if (/大纲重构: 失败/.test(line)) {
      updateStage(job, 'outline', { status: 'error', detail: '失败' });
    }

    // output path
    const mOut = line.match(/输出文件:\s*(.+\.json)\s*$/);
    if (mOut) {
      job.outputPath = mOut[1].trim();
      // derive log path from slug-timestamp naming
      try {
        const base = path.basename(job.outputPath); // slug-integrated-<ts>.json
        const dir = path.dirname(job.outputPath);
        const logName = base.replace(/\.json$/i, '.log');
        job.logPath = path.join(dir, logName);
        broadcast(job, 'file', { outPath: job.outputPath, logPath: job.logPath });
      } catch {}
    }
  } catch {}
}

export function startIntegrated(params: IntegratedParams) {
  const job = createJob('outline', {
    subject: params.subject,
    learningStyle: params.learningStyle,
    expectedContent: params.expectedContent,
  });

  const py = process.env.PYTHON || 'python';
  const script = path.join(repoRoot(), 'scripts', 'pipelines', 'langgraph', 'integrated_textbook_pipeline_chained.py');

  const args: string[] = [
    '-u',
    script,
    '--subject', params.subject,
    '--learning-style', params.learningStyle,
  ];
  if (params.expectedContent && params.expectedContent.trim()) {
    args.push('--expected-content', params.expectedContent.trim());
  }
  if (typeof params.topN === 'number') {
    args.push('--top-n', String(Math.max(1, params.topN)));
  }
  if (params.printPrompt) args.push('--print-prompt');
  if (params.debug) args.push('--debug'); else if (process.env.PIPELINE_LOG === '1') args.push('--log');
  if (params.geminiKey) args.push('--gemini-llm-key', params.geminiKey);
  if (params.kimiKey) args.push('--kimi-llm-key', params.kimiKey);

  const child = spawn(py, args, { cwd: repoRoot(), env: process.env });
  job.pid = child.pid;

  // 立即广播当前阶段为“运行中”，给前端即时反馈
  updateStage(job, 'collect', { status: 'running', detail: '启动脚本中…' });
  broadcast(job, 'log', { line: `[orchestrator] spawn: ${py} ${args.join(' ')}` });
  broadcast(job, 'log', { line: `[orchestrator] cwd: ${repoRoot()}` });

  child.on('spawn', () => {
    broadcast(job, 'log', { line: `[orchestrator] process started (pid=${child.pid})` });
  });

  const onData = (buf: Buffer) => {
    const text = buf.toString('utf-8');
    const lines = text.split(/\r?\n/);
    for (const line of lines) {
      if (!line) continue;
      broadcast(job, 'log', { line });
      parseLineForStages(job, line);
    }
  };
  child.stdout.on('data', onData);
  child.stderr.on('data', onData);

  child.on('close', (code) => {
    if (code === 0) {
      finishJob(job.id, 'success');
      broadcast(job, 'end', { status: 'success', outputPath: job.outputPath, logPath: job.logPath });
    } else {
      finishJob(job.id, 'error');
      broadcast(job, 'end', { status: 'error', message: `进程退出码 ${code}` });
    }
  });
  child.on('error', (err) => {
    finishJob(job.id, 'error');
    broadcast(job, 'log', { line: `[orchestrator] spawn error: ${String(err?.message || err)}` });
    broadcast(job, 'end', { status: 'error', message: String(err?.message || err) });
  });

  return job;
}

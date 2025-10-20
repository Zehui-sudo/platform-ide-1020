import { ReadableStreamDefaultController } from 'stream/web';

export type StageId = 'collect' | 'outline' | 'content';
export type StageStatus = 'pending' | 'running' | 'completed' | 'error';

export interface StageState {
  id: StageId;
  label: string;
  status: StageStatus;
  progress?: number; // 0-1
  detail?: string;
}

export interface SSEClient {
  id: string;
  controller: ReadableStreamDefaultController<Uint8Array>;
  send: (event: string, data: any) => void;
  close: () => void;
}

export interface JobRecord {
  id: string;
  type: 'outline' | 'content';
  pid?: number;
  status: 'running' | 'success' | 'error' | 'cancelled';
  startTs: number;
  endTs?: number;
  subject?: string;
  learningStyle?: string;
  expectedContent?: string;
  outputPath?: string;
  logPath?: string;
  // progress helpers for collect stage
  totalToFetch?: number;
  processed?: number;
  subscribers: Set<SSEClient>;
  stages: Record<StageId, StageState>;
}

// 使用全局 Map 跨路由/模块持久（Dev/HMR 下也尽量复用）
const g = globalThis as any;
if (!g.__PIPELINE_JOBS__) {
  g.__PIPELINE_JOBS__ = new Map<string, JobRecord>();
}
const jobs: Map<string, JobRecord> = g.__PIPELINE_JOBS__;

function makeId(prefix = 'job'): string {
  const rnd = Math.random().toString(36).slice(2, 8);
  const ts = Date.now().toString(36);
  return `${prefix}-${ts}-${rnd}`;
}

export function createJob(type: 'outline' | 'content', init?: Partial<JobRecord>): JobRecord {
  const id = makeId(type);
  const rec: JobRecord = {
    id,
    type,
    status: 'running',
    startTs: Date.now(),
    subscribers: new Set(),
    stages: {
      collect: { id: 'collect', label: '搜集参考教材', status: 'pending' },
      outline: { id: 'outline', label: '整合生成大纲', status: 'pending' },
      content: { id: 'content', label: '生成内容', status: 'pending' },
    },
    ...init,
  } as JobRecord;
  jobs.set(id, rec);
  return rec;
}

export function getJob(id: string): JobRecord | undefined {
  return jobs.get(id);
}

export function finishJob(id: string, status: JobRecord['status']): void {
  const rec = jobs.get(id);
  if (!rec) return;
  rec.status = status;
  rec.endTs = Date.now();
}

export function removeJob(id: string): void {
  jobs.delete(id);
}

export function attachSSE(job: JobRecord, controller: ReadableStreamDefaultController<Uint8Array>): SSEClient {
  const encoder = new TextEncoder();
  const client: SSEClient = {
    id: makeId('client'),
    controller,
    send: (event: string, data: any) => {
      try {
        const payload = typeof data === 'string' ? data : JSON.stringify(data);
        controller.enqueue(encoder.encode(`event: ${event}\n`));
        controller.enqueue(encoder.encode(`data: ${payload}\n\n`));
      } catch {}
    },
    close: () => {
      try { controller.close(); } catch {}
    },
  };
  job.subscribers.add(client);
  return client;
}

export function broadcast(job: JobRecord, event: string, data: any) {
  for (const sub of job.subscribers) {
    try { sub.send(event, data); } catch {}
  }
}

export function updateStage(job: JobRecord, id: StageId, patch: Partial<StageState>) {
  const prev = job.stages[id] || { id, label: id, status: 'pending' as StageStatus };
  job.stages[id] = { ...prev, ...patch, id } as StageState;
  broadcast(job, 'stage', job.stages[id]);
}

export function snapshot(job: JobRecord) {
  return {
    id: job.id,
    type: job.type,
    status: job.status,
    startTs: job.startTs,
    endTs: job.endTs,
    subject: job.subject,
    learningStyle: job.learningStyle,
    expectedContent: job.expectedContent,
    outputPath: job.outputPath,
    logPath: job.logPath,
    stages: job.stages,
  };
}

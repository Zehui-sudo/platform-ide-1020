console.log('[pipeline] jobManager loaded:', __filename);
import { ReadableStreamDefaultController } from 'stream/web';
import fs from 'fs/promises';
import fsSync from 'fs';
import path from 'path';

export type StageId = 'collect' | 'outline' | 'content';
export type StageStatus = 'pending' | 'running' | 'completed' | 'error';

export interface StageState {
  id: StageId;
  label: string;
  status: StageStatus;
  progress?: number; // 0-1
  detail?: string;
}

export type JobEventData = unknown;

export interface SSEClient {
  id: string;
  controller: ReadableStreamDefaultController<Uint8Array>;
  send: (event: string, data: JobEventData) => void;
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

interface PersistedJob {
  id: string;
  type: JobRecord['type'];
  pid?: number;
  status: JobRecord['status'];
  startTs: number;
  endTs?: number;
  subject?: string;
  learningStyle?: string;
  expectedContent?: string;
  outputPath?: string;
  logPath?: string;
  totalToFetch?: number;
  processed?: number;
  stages: Record<StageId, StageState>;
}

function repoRoot(): string {
  let dir = process.cwd();
  const seen = new Set<string>();
  while (!seen.has(dir)) {
    seen.add(dir);
    if (
      fsSync.existsSync(path.join(dir, 'config.json')) ||
      fsSync.existsSync(path.join(dir, 'package.json'))
    ) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (!parent || parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

const JOBS_STATE_DIR = path.join(repoRoot(), 'output', 'pipeline_jobs');
const JOBS_STATE_FILE = path.join(JOBS_STATE_DIR, 'jobs.json');

console.log('[pipeline] repoRoot resolved to:', repoRoot(), 'cwd:', process.cwd());

// 使用全局 Map 跨路由/模块持久（Dev/HMR 下也尽量复用）
type PipelineGlobal = typeof globalThis & {
  __PIPELINE_JOBS__?: Map<string, JobRecord>;
  __PIPELINE_JOBS_LOADED__?: boolean;
};

const pipelineGlobal = globalThis as PipelineGlobal;
if (!pipelineGlobal.__PIPELINE_JOBS__) {
  pipelineGlobal.__PIPELINE_JOBS__ = new Map<string, JobRecord>();
}
const jobs: Map<string, JobRecord> = pipelineGlobal.__PIPELINE_JOBS__;

function ensureStorageDirSync() {
  try {
    fsSync.mkdirSync(JOBS_STATE_DIR, { recursive: true });
  } catch {}
}

function serializeJob(job: JobRecord): PersistedJob {
  return {
    id: job.id,
    type: job.type,
    pid: job.pid,
    status: job.status,
    startTs: job.startTs,
    endTs: job.endTs,
    subject: job.subject,
    learningStyle: job.learningStyle,
    expectedContent: job.expectedContent,
    outputPath: job.outputPath,
    logPath: job.logPath,
    totalToFetch: job.totalToFetch,
    processed: job.processed,
    stages: job.stages,
  };
}

function hydrateJob(data: PersistedJob): JobRecord {
  const collect = data.stages?.collect ?? { id: 'collect', label: '搜集参考教材', status: 'pending' };
  const outline = data.stages?.outline ?? { id: 'outline', label: '整合生成大纲', status: 'pending' };
  const content = data.stages?.content ?? { id: 'content', label: '生成内容', status: 'pending' };

  const record: JobRecord = {
    id: data.id,
    type: data.type,
    pid: data.pid,
    status: data.status,
    startTs: data.startTs,
    endTs: data.endTs,
    subject: data.subject,
    learningStyle: data.learningStyle,
    expectedContent: data.expectedContent,
    outputPath: data.outputPath,
    logPath: data.logPath,
    totalToFetch: data.totalToFetch,
    processed: data.processed,
    subscribers: new Set<SSEClient>(),
    stages: {
      collect: { label: '搜集参考教材', ...collect, id: 'collect' },
      outline: { label: '整合生成大纲', ...outline, id: 'outline' },
      content: { label: '生成内容', ...content, id: 'content' },
    },
  };
  return record;
}

function flushJobsToDiskSync() {
  try {
    ensureStorageDirSync();
    const payload = Array.from(jobs.values()).map(serializeJob);
    const json = JSON.stringify(payload, null, 2);
    fsSync.writeFileSync(JOBS_STATE_FILE, json, { encoding: 'utf-8' });
    console.log('[pipeline] jobs persisted:', JOBS_STATE_FILE, 'items=', payload.length);
  } catch (error) {
    console.error('[pipeline] Failed to persist jobs:', error);
  }
}

async function loadJobsFromDisk() {
  if (pipelineGlobal.__PIPELINE_JOBS_LOADED__) return;
  pipelineGlobal.__PIPELINE_JOBS_LOADED__ = true;
  try {
    const text = await fs.readFile(JOBS_STATE_FILE, { encoding: 'utf-8' });
    const parsed = JSON.parse(text) as PersistedJob[];
    if (Array.isArray(parsed)) {
      for (const item of parsed) {
        if (!item?.id || !item?.type) continue;
        if (!jobs.has(item.id)) {
          jobs.set(item.id, hydrateJob(item));
        } else {
          const existing = jobs.get(item.id);
          if (existing) {
            existing.pid = item.pid;
            existing.status = item.status;
            existing.startTs = item.startTs;
            existing.endTs = item.endTs;
            existing.subject = item.subject;
            existing.learningStyle = item.learningStyle;
            existing.expectedContent = item.expectedContent;
            existing.outputPath = item.outputPath;
            existing.logPath = item.logPath;
            existing.totalToFetch = item.totalToFetch;
            existing.processed = item.processed;
            existing.stages = hydrateJob(item).stages;
          }
        }
      }
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== 'ENOENT') {
      console.error('[pipeline] Failed to load jobs:', error);
    }
  }
}
void loadJobsFromDisk();

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
  console.log('[pipeline] createJob:', id, type, 'subject=', init?.subject, 'cwd=', process.cwd(), 'repoRoot=', repoRoot());
  console.log('[pipeline] createJob stages:', rec.stages);
  flushJobsToDiskSync();
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
  console.log('[pipeline] finishJob:', id, 'status=', status, 'endTs=', rec.endTs);
  flushJobsToDiskSync();
}

export function removeJob(id: string): void {
  jobs.delete(id);
  flushJobsToDiskSync();
}

export function attachSSE(job: JobRecord, controller: ReadableStreamDefaultController<Uint8Array>): SSEClient {
  const encoder = new TextEncoder();
  console.log('[pipeline] attachSSE: job=', job.id, 'currentSubscribers=', job.subscribers.size);
  const client: SSEClient = {
    id: makeId('client'),
    controller,
    send: (event: string, data: JobEventData) => {
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

export function broadcast(job: JobRecord, event: string, data: JobEventData) {
  for (const sub of job.subscribers) {
    try { sub.send(event, data); } catch {}
  }
}

export function updateStage(job: JobRecord, id: StageId, patch: Partial<StageState>) {
  const prev = job.stages[id] || { id, label: id, status: 'pending' as StageStatus };
  job.stages[id] = { ...prev, ...patch, id } as StageState;
  console.log('[pipeline] updateStage:', job.id, 'stage=', id, 'patch=', patch);
  broadcast(job, 'stage', job.stages[id]);
  flushJobsToDiskSync();
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

export function listJobs(): JobRecord[] {
  return Array.from(jobs.values());
}

export function latestJob(type: JobRecord['type']): JobRecord | undefined {
  let latest: JobRecord | undefined;
  for (const job of jobs.values()) {
    if (job.type !== type) continue;
    if (!latest || job.startTs > latest.startTs) {
      latest = job;
    }
  }
  return latest;
}

export function touchJob(job: JobRecord): void {
  if (!jobs.has(job.id)) {
    jobs.set(job.id, job);
    console.log('[pipeline] touchJob: add missing job', job.id);
  } else {
    console.log('[pipeline] touchJob: refresh job', job.id);
  }
  flushJobsToDiskSync();
}

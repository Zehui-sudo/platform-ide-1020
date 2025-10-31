import { NextResponse } from 'next/server';
import { spawn } from 'node:child_process';
import { promises as fsp } from 'node:fs';
import path from 'node:path';
import type { LearningConfigSnapshot } from '@/types';

export const runtime = 'nodejs';

const LOCK_KEY = '__learningConfigRefreshLock__';
const PROJECT_ROOT = process.cwd();
const SCRIPT_PATH = path.join(PROJECT_ROOT, 'scripts', 'generate-learn-data.mjs');
const CONFIG_PATH = path.join(PROJECT_ROOT, 'public', 'learn-data', 'learning-config.json');

type RefreshPayload = {
  slug?: unknown;
  subject?: unknown;
  slugs?: unknown;
  publishDir?: unknown;
  path?: unknown;
};

type RefreshResult = {
  status: 'ok' | 'noop';
  processed: string[];
  skipped: Array<{ slug: string; reason?: string }>;
  config: LearningConfigSnapshot;
};

const enqueueExclusive = async <T>(task: () => Promise<T>): Promise<T> => {
  const globalScope = globalThis as unknown as Record<string, Promise<unknown> | undefined>;
  const current = globalScope[LOCK_KEY] ?? Promise.resolve();
  const next = current.then(task);
  globalScope[LOCK_KEY] = next.catch(() => {});
  return next;
};

const normalizeSlug = (value: unknown): string | null => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const extractSlugFromPath = (value: unknown): string | null => {
  if (typeof value !== 'string') return null;
  const parts = value.split(/[\\/]+/).filter(Boolean);
  if (parts.length === 0) return null;
  const idx = parts.lastIndexOf('content');
  if (idx >= 0 && idx + 1 < parts.length) {
    return parts[idx + 1];
  }
  return parts[parts.length - 1] ?? null;
};

const runGenerator = (slugs: string[]) =>
  new Promise<{ stdout: string; stderr: string }>((resolve, reject) => {
    const args = [SCRIPT_PATH, `--subjects=${slugs.join(',')}`, '--no-clean'];
    const child = spawn('node', args, {
      cwd: PROJECT_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    child.stdout?.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr?.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('error', (error) => {
      reject(error);
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        const err = new Error(`generate-learn-data exited with code ${code}`);
        (err as Error & { stdout?: string; stderr?: string }).stdout = stdout;
        (err as Error & { stdout?: string; stderr?: string }).stderr = stderr;
        reject(err);
      }
    });
  });

const readLearningConfig = async (): Promise<LearningConfigSnapshot | null> => {
  try {
    const raw = await fsp.readFile(CONFIG_PATH, 'utf8');
    return JSON.parse(raw) as LearningConfigSnapshot;
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException)?.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
};

export async function POST(request: Request) {
  let payload: RefreshPayload;
  try {
    payload = (await request.json()) as RefreshPayload;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON payload' }, { status: 400 });
  }

  const slugSet = new Set<string>();
  const pushSlug = (candidate: string | null) => {
    if (candidate) slugSet.add(candidate);
  };

  pushSlug(normalizeSlug(payload.slug));
  pushSlug(normalizeSlug(payload.subject));
  if (Array.isArray(payload.slugs)) {
    for (const item of payload.slugs) {
      pushSlug(normalizeSlug(item));
    }
  }
  pushSlug(extractSlugFromPath(payload.publishDir));
  pushSlug(extractSlugFromPath(payload.path));

  if (slugSet.size === 0) {
    return NextResponse.json({ error: 'Missing subject slug' }, { status: 400 });
  }

  try {
    const slugs = Array.from(slugSet);
    const result = await enqueueExclusive<RefreshResult>(async () => {
      const existingConfig =
        (await readLearningConfig()) ?? {
          generatedAt: new Date().toISOString(),
          subjects: [],
          pathMap: {},
          labelMap: {},
        };

      const alreadyAvailable = slugs.every((slug) =>
        (existingConfig.subjects ?? []).includes(slug),
      );
      if (alreadyAvailable) {
        return {
          status: 'noop',
          processed: [],
          skipped: [],
          config: existingConfig,
        } satisfies RefreshResult;
      }

      try {
        await fsp.access(SCRIPT_PATH);
      } catch {
        throw new Error('generate-learn-data script not found');
      }

      await runGenerator(slugs);
      const updatedConfig =
        (await readLearningConfig()) ??
        existingConfig;

      const availableSubjects = updatedConfig.subjects ?? [];
      const processed = slugs.filter((slug) => availableSubjects.includes(slug));
      const skipped = slugs
        .filter((slug) => !availableSubjects.includes(slug))
        .map((slug) => ({ slug, reason: 'missing-learning-path' }));

      const status: RefreshResult['status'] =
        processed.length > 0 ? 'ok' : 'noop';

      return {
        status,
        processed,
        skipped,
        config: updatedConfig,
      } satisfies RefreshResult;
    });

    const statusCode =
      result.status === 'ok' || result.status === 'noop' ? 200 : 404;
    return NextResponse.json(result, { status: statusCode });
  } catch (error) {
    console.error('[learning-config/refresh] 发生错误', error);
    return NextResponse.json(
      { error: 'Failed to refresh learning config' },
      { status: 500 },
    );
  }
}

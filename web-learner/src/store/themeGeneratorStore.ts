import { create } from 'zustand';
import { useLearningStore } from '@/store/learningStore';

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? '').replace(/\/$/, '');
const apiUrl = (path: string) => `${API_BASE}${path}`;

type StageStatus = 'pending' | 'running' | 'completed' | 'error';

interface SnapshotStage {
  id: string;
  label: string;
  status: StageStatus;
  detail?: string;
  progress?: number;
}

interface PipelineJobSnapshot {
  id: string;
  type: 'outline' | 'content';
  status: 'running' | 'success' | 'error' | 'cancelled';
  startTs: number;
  endTs?: number;
  subject?: string;
  learningStyle?: string;
  expectedContent?: string;
  outputPath?: string;
  logPath?: string;
  stages: {
    collect?: SnapshotStage;
    outline?: SnapshotStage;
    content?: SnapshotStage;
    [key: string]: SnapshotStage | undefined;
  };
}

interface OutlineSectionSummary {
  id?: string;
  title?: string;
}

interface OutlineGroupSummary {
  id?: string;
  title?: string;
  sections?: OutlineSectionSummary[];
}

interface ReconstructedOutline {
  title?: string;
  groups?: OutlineGroupSummary[];
  chapters?: OutlineGroupSummary[];
  sections?: OutlineSectionSummary[];
  meta?: {
    topic_slug?: string;
  };
}

interface OutlineResultPayload {
  reconstructed_outline?: ReconstructedOutline | null;
  subject_slug?: string;
}

interface ContentResultPayload {
  reportPath?: string | null;
  publishedFiles?: string[] | null;
  status?: string;
  subject?: string;
  logPath?: string | null;
  publishDir?: string | null;
}

interface JobStartResponse {
  jobId: string;
}

const countSections = (groups?: OutlineGroupSummary[] | null): number => {
  if (!Array.isArray(groups)) {
    return 0;
  }

  return groups.reduce((accumulator, group) => {
    const sectionCount = Array.isArray(group?.sections) ? group.sections.length : 0;
    return accumulator + sectionCount;
  }, 0);
};

const estimateSectionTotal = (outline: ReconstructedOutline | null | undefined): number => {
  if (!outline) {
    return 0;
  }

  if (Array.isArray(outline.groups) && outline.groups.length > 0) {
    return countSections(outline.groups);
  }

  if (Array.isArray(outline.chapters) && outline.chapters.length > 0) {
    return countSections(outline.chapters);
  }

  if (Array.isArray(outline.sections)) {
    return outline.sections.length;
  }

  return 0;
};

interface StageState {
  status: StageStatus;
  detail?: string;
  progress?: number;
}

export type GenerationStage = 'idle' | 'generating_outline' | 'outline_ready' | 'generating_content' | 'content_ready';

interface ThemeGeneratorState {
  // Stage and inputs
  stage: GenerationStage;
  themeName: string;
  generationStyle: 'principle' | 'preview';
  content: string;

  // Job and results
  jobId: string | null;
  contentJobId: string | null;
  outlineInputPath: string | null;
  outlineResult: OutlineResultPayload | null;
  contentResult: ContentResultPayload | null;
  // Estimated totals for progress tracking
  contentTotal: number | null;
  contentSaved: number | null;

  // UI State
  logs: string[];
  showLogs: boolean;
  isSubscribing: boolean;
  uiOpen: boolean;

  // Progress tracking
  collectStage: StageState;
  outlineStage: StageState;
  contentStage: StageState;

  // Actions
  setFormField: <K extends keyof ThemeGeneratorState>(field: K, value: ThemeGeneratorState[K]) => void;
  setUiOpen: (open: boolean) => void;
  startOutlineGeneration: () => Promise<void>;
  startContentGeneration: () => Promise<void>;
  subscribeToOutline: (jobId: string) => void;
  subscribeToContent: (jobId: string) => void;
  cancelContentGeneration: () => Promise<void>;
  cancelOutlineGeneration: () => Promise<void>;
  loadCourse: () => Promise<void>;
  reset: () => void;
  restartFlow: (options?: { keepInputs?: boolean }) => void;
  rehydrate: () => Promise<void>;
}

// Keep EventSource instances outside of the store state
let outlineEvtSrc: EventSource | null = null;
let contentEvtSrc: EventSource | null = null;

type ThemeGeneratorData = Omit<
  ThemeGeneratorState,
  | 'setFormField'
  | 'setUiOpen'
  | 'startOutlineGeneration'
  | 'startContentGeneration'
  | 'subscribeToOutline'
  | 'subscribeToContent'
  | 'cancelContentGeneration'
  | 'cancelOutlineGeneration'
  | 'loadCourse'
  | 'reset'
  | 'restartFlow'
  | 'rehydrate'
>;

const createInitialState = (): ThemeGeneratorData => ({
  stage: 'idle',
  themeName: '',
  generationStyle: 'principle',
  content: '',
  jobId: null,
  contentJobId: null,
  outlineInputPath: null,
  outlineResult: null,
  contentResult: null,
  contentTotal: null,
  contentSaved: null,
  logs: [],
  showLogs: false,
  isSubscribing: false,
  uiOpen: false,
  collectStage: { status: 'pending' },
  outlineStage: { status: 'pending' },
  contentStage: { status: 'pending' },
});

const clampProgress = (value?: number): number | undefined =>
  typeof value === 'number' ? Math.max(0, Math.min(1, value)) : undefined;

const toStageState = (stage?: SnapshotStage): StageState => ({
  status: stage?.status ?? 'pending',
  detail: stage?.detail,
  progress: clampProgress(stage?.progress),
});

const parseSavedFromDetail = (detail?: string): number | null => {
  if (!detail) return null;
  const m = detail.match(/已保存\s*(\d+)\s*个/);
  if (m) return parseInt(m[1], 10);
  return null;
};

const DISMISSED_JOBS_STORAGE_KEY = 'themeGenerator:dismissedJobs';

const loadDismissedJobIds = (): Set<string> => {
  if (typeof window === 'undefined') {
    return new Set();
  }
  try {
    const raw = window.localStorage.getItem(DISMISSED_JOBS_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      const ids = parsed
        .map((id) => (typeof id === 'string' ? id.trim() : ''))
        .filter((id): id is string => !!id);
      return new Set(ids);
    }
  } catch {}
  return new Set();
};

const storeDismissedJobIds = (ids: Set<string>) => {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    const ordered = Array.from(ids).filter((id) => !!id);
    const limited = ordered.slice(-20);
    window.localStorage.setItem(
      DISMISSED_JOBS_STORAGE_KEY,
      JSON.stringify(limited),
    );
  } catch {}
};

const rememberDismissedJobs = (jobIds: (string | null | undefined)[]) => {
  if (typeof window === 'undefined') {
    return;
  }
  const existing = loadDismissedJobIds();
  let changed = false;
  for (const jobId of jobIds) {
    if (typeof jobId === 'string') {
      const trimmed = jobId.trim();
      if (trimmed && !existing.has(trimmed)) {
        existing.add(trimmed);
        changed = true;
      }
    }
  }
  if (changed) {
    storeDismissedJobIds(existing);
  }
};

export const useThemeGeneratorStore = create<ThemeGeneratorState>()((set, get) => ({
  ...createInitialState(),

  setFormField: (field, value) =>
    set({ [field]: value } as Partial<ThemeGeneratorState>),

  setUiOpen: (open) => set({ uiOpen: open }),

  subscribeToOutline: (jobId) => {
    if (outlineEvtSrc) {
      outlineEvtSrc.close();
    }
    set({ isSubscribing: true, logs: [] });

        const es = new EventSource(apiUrl(`/api/outline/stream?jobId=${encodeURIComponent(jobId)}`));
    outlineEvtSrc = es;

    es.addEventListener('file', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data) as { outPath?: string };
        if (data?.outPath) {
          set({ outlineInputPath: data.outPath });
        }
      } catch {}
    });

    es.addEventListener('log', (ev: MessageEvent) => {
      const rawData = typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data);
      let line = rawData;
      try {
        const parsed = JSON.parse(rawData) as { line?: string };
        line = parsed.line ?? rawData;
      } catch {}
      set((state) => ({ logs: [...state.logs.slice(-500), line] }));
    });

    es.addEventListener('hello', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const snap = data?.snapshot || {};
        const stages = snap?.stages || {};
        set((state) => ({
          collectStage: toStageState(stages.collect),
          outlineStage: toStageState(stages.outline),
          outlineInputPath: typeof snap.outputPath === 'string' ? snap.outputPath : state.outlineInputPath,
        }));
      } catch {}
    });

    es.addEventListener('stage', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        if (data?.id === 'collect') {
          set({ collectStage: toStageState(data as SnapshotStage) });
        } else if (data?.id === 'outline') {
          set({ outlineStage: toStageState(data as SnapshotStage) });
        }
      } catch {}
    });

    es.addEventListener('end', async (ev: MessageEvent) => {
      es.close();
      outlineEvtSrc = null;
      try {
        const data = JSON.parse(ev.data);
        if (data?.outputPath) {
          set({ outlineInputPath: data.outputPath });
        }
        if (data?.status === 'success') {
            const r = await fetch(apiUrl(`/api/outline/result?jobId=${encodeURIComponent(jobId)}`), { cache: 'no-store' });
          if (r.ok) {
            const result = (await r.json()) as OutlineResultPayload;
            set({
              outlineResult: result,
              stage: 'outline_ready',
              isSubscribing: false,
            });
          } else {
            set({ stage: 'idle', isSubscribing: false });
          }
        } else {
          set({ stage: 'idle', isSubscribing: false });
        }
      } catch {
        set({ stage: 'idle', isSubscribing: false });
      }
    });

    es.onerror = () => {
      // keep connection alive for auto-retry
    };
  },

  startOutlineGeneration: async () => {
    const { themeName, generationStyle, content } = get();
    if (!themeName.trim() || !content.trim()) return;

    set({
      stage: 'generating_outline',
      logs: [],
      collectStage: { status: 'pending' },
      outlineStage: { status: 'pending' },
      outlineResult: null,
      outlineInputPath: null,
      jobId: null,
    });

    try {
      const styleMap = { principle: 'principles', preview: 'deep_preview' };
          const res = await fetch(apiUrl('/api/outline/start'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: themeName.trim(),
          learningStyle: styleMap[generationStyle],
          expectedContent: content.trim(),
          topN: 3,
          printPrompt: true,
          debug: false,
        }),
      });

      if (!res.ok) {
        let message = `Failed to start job: ${res.status}`;
        try {
          const data = await res.json();
          message = String(
            (data as { detail?: string; error?: string })?.detail ??
              (data as { error?: string })?.error ??
              message,
          );
        } catch {}
        throw new Error(message);
      }
          const { jobId } = (await res.json()) as JobStartResponse;
      set({ jobId });
      get().subscribeToOutline(jobId);
    } catch (error) {
      console.error('Failed to generate theme:', error);
      const detail = error instanceof Error ? error.message : '无法启动大纲生成任务';
      set({
        stage: 'idle',
        collectStage: { status: 'error', detail },
        outlineStage: { status: 'error', detail },
        isSubscribing: false,
      });
    }
  },

  subscribeToContent: (jobId: string) => {
    if (contentEvtSrc) {
      contentEvtSrc.close();
    }
    set({ isSubscribing: true, logs: [] });

        const es = new EventSource(apiUrl(`/api/content/stream?jobId=${encodeURIComponent(jobId)}`));
    contentEvtSrc = es;

    es.addEventListener('hello', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const snap = data?.snapshot || {};
        const st = snap?.stages?.content as SnapshotStage | undefined;
        if (st) {
          let saved: number | undefined;
          const m = typeof st.detail === 'string' ? st.detail.match(/已保存\s*(\d+)\s*个/) : null;
          if (m) saved = parseInt(m[1], 10);
          set((state) => {
            const total = state.contentTotal;
            const progress =
              typeof saved === 'number' && typeof total === 'number' && total > 0
                ? Math.max(0, Math.min(1, saved / total))
                : st.progress;
            return {
              contentSaved: typeof saved === 'number' ? saved : state.contentSaved,
              contentStage: { status: st.status, detail: st.detail, progress },
            };
          });
        }
      } catch {}
    });

    es.addEventListener('stage', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        if (data?.id === 'content') {
          let saved: number | undefined;
          const m = typeof data.detail === 'string' ? data.detail.match(/已保存\s*(\d+)\s*个/) : null;
          if (m) saved = parseInt(m[1], 10);
          set((state) => {
            const total = state.contentTotal;
            const progress =
              typeof saved === 'number' && typeof total === 'number' && total > 0
                ? Math.max(0, Math.min(1, saved / total))
                : data.progress;
            return {
              contentSaved: typeof saved === 'number' ? saved : state.contentSaved,
              contentStage: {
                status: data.status as StageStatus,
                detail: data.detail,
                progress: clampProgress(progress),
              },
            };
          });
        }
      } catch {}
    });

    es.addEventListener('log', (ev: MessageEvent) => {
      const rawData = typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data);
      let line = rawData;
      try {
        const parsed = JSON.parse(rawData) as { line?: string };
        line = parsed.line ?? rawData;
      } catch {}
      set((prev) => ({ logs: [...prev.logs.slice(-500), line] }));
    });

    es.addEventListener('end', async (ev: MessageEvent) => {
      es.close();
      contentEvtSrc = null;
      try {
        const data = JSON.parse(ev.data);
        if (data?.status === 'success') {
                const r = await fetch(apiUrl(`/api/content/result?jobId=${encodeURIComponent(jobId)}`), { cache: 'no-store' });
          if (r.ok) {
            const result = (await r.json()) as ContentResultPayload;
            set({ contentResult: result, stage: 'content_ready', isSubscribing: false });
          } else {
            set({ stage: 'outline_ready', isSubscribing: false });
          }
        } else {
          set({ stage: 'outline_ready', isSubscribing: false });
        }
      } catch {
        set({ stage: 'outline_ready', isSubscribing: false });
      }
    });

    es.onerror = () => {
      // keep connection alive for auto-retry
    };
  },

  startContentGeneration: async () => {
    const { jobId, outlineResult, outlineInputPath } = get();
    if (!jobId) return;

    const outline = outlineResult?.reconstructed_outline ?? null;
    const total = estimateSectionTotal(outline);

    set({
      stage: 'generating_content',
      contentStage: { status: 'running', detail: 'Initializing script...', progress: total > 0 ? 0 : undefined },
      contentResult: null,
      logs: [],
      contentTotal: total || null,
      contentSaved: 0,
    });

    try {
          const res = await fetch(apiUrl('/api/content/start'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          refJobId: jobId,
          inputPath: outlineInputPath ?? undefined,
          debug: true,
        }),
      });

      if (!res.ok) {
        let message = `Failed to start content generation: ${res.status}`;
        try {
          const data = await res.json();
          message = String(
            (data as { detail?: string; error?: string })?.detail ??
              (data as { error?: string })?.error ??
              message,
          );
        } catch {}
        throw new Error(message);
      }
      const { jobId: cJobId } = (await res.json()) as JobStartResponse;
      set({ contentJobId: cJobId });
      get().subscribeToContent(cJobId);
    } catch (error) {
      console.error(error);
      const detail = error instanceof Error ? error.message : '无法启动章节生成任务';
      set({
        stage: 'outline_ready',
        contentStage: { status: 'error', detail },
        isSubscribing: false,
      });
    }
  },

  cancelContentGeneration: async () => {
    const { contentJobId } = get();
    if (!contentJobId) return;
    try {
          await fetch(apiUrl(`/api/content/cancel?jobId=${encodeURIComponent(contentJobId)}`), { method: 'POST' });
    } catch {}
    if (contentEvtSrc) {
      contentEvtSrc.close();
      contentEvtSrc = null;
    }
    set({ stage: 'outline_ready', isSubscribing: false });
  },

  cancelOutlineGeneration: async () => {
    const { jobId } = get();
    if (!jobId) return;
    try {
          await fetch(apiUrl(`/api/outline/cancel?jobId=${encodeURIComponent(jobId)}`), { method: 'POST' });
    } catch {}
    if (outlineEvtSrc) {
      outlineEvtSrc.close();
      outlineEvtSrc = null;
    }
    set({ stage: 'idle', isSubscribing: false });
  },

  loadCourse: async () => {
    const { contentResult, outlineResult } = get();
    try {
      const pub = contentResult?.publishDir;
      const getSlug = () => {
        if (pub) {
          const parts = String(pub).split(/[\/]+/);
          const ix = parts.lastIndexOf('content');
          if (ix >= 0 && ix + 1 < parts.length) return parts[ix + 1];
        }
        return (
          outlineResult?.reconstructed_outline?.meta?.topic_slug ||
          outlineResult?.subject_slug ||
          ''
        );
      };
      const slug = getSlug();
      if (slug) {
        const store = useLearningStore.getState();
        const subjects = store.availableSubjects;
        if (!subjects || !subjects.includes(slug)) {
          try {
            await store.refreshLearningConfig({ slugs: [slug], force: true });
          } catch (error) {
            console.warn('[themeGeneratorStore] refreshLearningConfig failed', error);
          }
        }
        await store.loadPath(slug);
        let loadedPath = useLearningStore.getState().currentPath;
        if (!loadedPath || loadedPath.subject !== slug) {
          try {
            await store.refreshLearningConfig({ slugs: [slug], force: true });
          } catch (error) {
            console.warn('[themeGeneratorStore] 二次 refreshLearningConfig 失败', error);
          }
          await store.loadPath(slug);
        }
      }
    } catch {}
  },

  reset: () => {
    if (outlineEvtSrc) outlineEvtSrc.close();
    if (contentEvtSrc) contentEvtSrc.close();
    outlineEvtSrc = null;
    contentEvtSrc = null;
    const { jobId, contentJobId } = get();
    rememberDismissedJobs([jobId, contentJobId]);
    set(() => ({ ...createInitialState() }));
  },

  restartFlow: (options) => {
    if (outlineEvtSrc) outlineEvtSrc.close();
    if (contentEvtSrc) contentEvtSrc.close();
    outlineEvtSrc = null;
    contentEvtSrc = null;
    const { keepInputs = false } = options ?? {};
    const { jobId, contentJobId, themeName, generationStyle, content } = get();
    rememberDismissedJobs([jobId, contentJobId]);
    set(() => ({
      ...createInitialState(),
      ...(keepInputs ? { themeName, generationStyle, content } : {}),
      stage: 'idle',
    }));
  },

  rehydrate: async () => {
    try {
      const dismissed = loadDismissedJobIds();

      const [outlineResp, contentResp] = await Promise.all([
        fetch(apiUrl('/api/pipeline/jobs/latest?type=outline'), { cache: 'no-store' }).catch(() => null),
        fetch(apiUrl('/api/pipeline/jobs/latest?type=content'), { cache: 'no-store' }).catch(() => null),
      ]);

      const outlineData = outlineResp && outlineResp.ok ? await outlineResp.json() : null;
      const contentData = contentResp && contentResp.ok ? await contentResp.json() : null;

      const rawOutlineJob = (outlineData?.job ?? null) as PipelineJobSnapshot | null;
      const rawContentJob = (contentData?.job ?? null) as PipelineJobSnapshot | null;

      const outlineDismissed = !!rawOutlineJob && dismissed.has(rawOutlineJob.id);
      const contentDismissed = !!rawContentJob && dismissed.has(rawContentJob.id);

      const outlineJob = outlineDismissed ? null : rawOutlineJob;
      let contentJob = contentDismissed ? null : rawContentJob;

      const targetSubject =
        outlineJob?.subject?.trim() ||
        rawOutlineJob?.subject?.trim() ||
        rawContentJob?.subject?.trim() ||
        null;

      if (
        contentJob &&
        targetSubject &&
        contentJob.subject &&
        contentJob.subject.trim() !== targetSubject
      ) {
        contentJob = null;
      }

      const outlineResultPromise =
        outlineJob && outlineJob.status === 'success'
          ? fetch(apiUrl(`/api/outline/result?jobId=${encodeURIComponent(outlineJob.id)}`), { cache: 'no-store' })
              .then((res) => (res.ok ? res.json() : null))
              .catch(() => null)
          : Promise.resolve(null);

      const contentResultPromise =
        contentJob && contentJob.status === 'success'
          ? fetch(apiUrl(`/api/content/result?jobId=${encodeURIComponent(contentJob.id)}`), { cache: 'no-store' })
              .then((res) => (res.ok ? res.json() : null))
              .catch(() => null)
          : Promise.resolve(null);

      const [outlineResult, contentResult] = await Promise.all([
        outlineResultPromise,
        contentResultPromise,
      ]);

      let inferredStage: GenerationStage = 'idle';
      if (contentJob) {
        if (contentJob.status === 'running') inferredStage = 'generating_content';
        else if (contentJob.status === 'success') inferredStage = 'content_ready';
        else if (contentJob.status === 'error') inferredStage = 'outline_ready';
      }
      if (inferredStage === 'idle' && outlineJob) {
        if (outlineJob.status === 'running') inferredStage = 'generating_outline';
        else if (outlineJob.status === 'success') inferredStage = 'outline_ready';
      }

      const savedFromContent = parseSavedFromDetail(contentJob?.stages?.content?.detail);

      set((state) => ({
        ...state,
        logs: [],
        isSubscribing: false,
        jobId: outlineJob?.id ?? null,
        contentJobId: contentJob?.id ?? null,
        outlineInputPath: outlineJob?.outputPath ?? null,
        collectStage: toStageState(outlineJob?.stages?.collect),
        outlineStage: toStageState(outlineJob?.stages?.outline),
        contentStage: toStageState(contentJob?.stages?.content),
        outlineResult: (outlineResult ?? state.outlineResult) as OutlineResultPayload | null,
        contentResult: contentJob ? ((contentResult ?? state.contentResult) as ContentResultPayload | null) : null,
        stage: inferredStage,
        contentSaved: savedFromContent ?? (state.contentSaved ?? null),
        contentTotal: state.contentTotal,
      }));

      if (outlineJob?.status === 'running') {
        get().subscribeToOutline(outlineJob.id);
      }
      if (contentJob?.status === 'running') {
        get().subscribeToContent(contentJob.id);
      }
    } catch (error) {
      console.error('Failed to rehydrate theme generator state', error);
    }
  },
}));

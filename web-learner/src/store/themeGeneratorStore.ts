import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { useLearningStore } from '@/store/learningStore';

type StageStatus = 'pending' | 'running' | 'completed' | 'error';

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
  loadCourse: () => void;
  reset: () => void;
  rehydrate: () => void;
}

// Keep EventSource instances outside of the persisted state
let outlineEvtSrc: EventSource | null = null;
let contentEvtSrc: EventSource | null = null;

const initialState = {
  stage: 'idle' as GenerationStage,
  themeName: '',
  generationStyle: 'principle' as 'principle' | 'preview',
  content: '',
  jobId: null,
  contentJobId: null,
  outlineResult: null,
  contentResult: null,
  contentTotal: null,
  contentSaved: null,
  logs: [],
  showLogs: false,
  isSubscribing: false,
  uiOpen: false,
  collectStage: { status: 'pending' } as StageState,
  outlineStage: { status: 'pending' } as StageState,
  contentStage: { status: 'pending' } as StageState,
};

export const useThemeGeneratorStore = create<ThemeGeneratorState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setFormField: (field, value) => set({ [field]: value }),
      setUiOpen: (open) => set({ uiOpen: open }),

      subscribeToOutline: (jobId) => {
        if (outlineEvtSrc) {
          outlineEvtSrc.close();
        }
        set({ isSubscribing: true, logs: [] });

        const es = new EventSource(`/api/outline/stream?jobId=${encodeURIComponent(jobId)}`);
        outlineEvtSrc = es;
        
        es.addEventListener('log', (ev: MessageEvent) => {
          const rawData = typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data);
          let line = rawData;
          try {
            const parsed = JSON.parse(rawData) as { line?: string };
            line = parsed.line ?? rawData;
          } catch {
            // Keep raw string when parsing fails.
          }
          set((state) => ({ logs: [...state.logs.slice(-500), line] }));
        });
        
        es.addEventListener('hello', (ev: MessageEvent) => {
          const data = JSON.parse(ev.data);
          const snap = data?.snapshot || {};
          if (snap?.stages) {
            const stc = snap.stages.collect;
            const sto = snap.stages.outline;
            if (stc) set({ collectStage: { status: stc.status, detail: stc.detail, progress: stc.progress } });
            if (sto) set({ outlineStage: { status: sto.status, detail: sto.detail } });
          }
          // 若任务已结束，服务端会紧跟着发送 end 事件，这里不提前切换阶段
        });

        es.addEventListener('stage', (ev: MessageEvent) => {
          const data = JSON.parse(ev.data);
          if (data?.id === 'collect') {
            set({ collectStage: { status: data.status, detail: data.detail, progress: typeof data.progress === 'number' ? Math.max(0, Math.min(1, data.progress)) : undefined } });
          } else if (data?.id === 'outline') {
            set({ outlineStage: { status: data.status, detail: data.detail } });
          }
        });

        es.addEventListener('end', async (ev: MessageEvent) => {
          es.close();
          outlineEvtSrc = null;
          const data = JSON.parse(ev.data);
          if (data?.status === 'success') {
            const r = await fetch(`/api/outline/result?jobId=${encodeURIComponent(jobId)}`, { cache: 'no-store' });
            if (r.ok) {
              const result = (await r.json()) as OutlineResultPayload;
              set({ outlineResult: result, stage: 'outline_ready', isSubscribing: false });
            } else {
              set({ stage: 'idle', isSubscribing: false });
            }
          } else {
            set({ stage: 'idle', isSubscribing: false });
          }
        });

        // 允许 EventSource 自动重连，不在错误时主动关闭或重置阶段
        es.onerror = () => {
          // 保持订阅与阶段，等待自动重连
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
          jobId: null,
        });

        try {
          const styleMap = { principle: 'principles', preview: 'deep_preview' };
          const res = await fetch('/api/outline/start', {
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
              message = String((data as { detail?: string; error?: string })?.detail ?? (data as { error?: string })?.error ?? message);
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

        const es = new EventSource(`/api/content/stream?jobId=${encodeURIComponent(jobId)}`);
        contentEvtSrc = es;

        es.addEventListener('hello', (ev: MessageEvent) => {
            const data = JSON.parse(ev.data);
            const snap = data?.snapshot || {};
            if (snap?.stages?.content) {
              const st = snap.stages.content;
              // Try infer saved count from detail
              let saved: number | undefined;
              const m = typeof st.detail === 'string' ? st.detail.match(/已保存\s*(\d+)\s*个/) : null;
              if (m) saved = parseInt(m[1], 10);
              set((state) => {
                const total = state.contentTotal;
                const progress = (typeof saved === 'number' && typeof total === 'number' && total > 0)
                  ? Math.max(0, Math.min(1, saved / total))
                  : st.progress;
                return {
                  contentSaved: typeof saved === 'number' ? saved : state.contentSaved,
                  contentStage: { status: st.status, detail: st.detail, progress },
                };
              });
            }
            // 不在 hello 时切换阶段，等待 end 事件统一处理
        });

        es.addEventListener('stage', (ev: MessageEvent) => {
            const data = JSON.parse(ev.data);
            if (data?.id === 'content') {
              let saved: number | undefined;
              const m = typeof data.detail === 'string' ? data.detail.match(/已保存\s*(\d+)\s*个/) : null;
              if (m) saved = parseInt(m[1], 10);
              set((state) => {
                const total = state.contentTotal;
                const progress = (typeof saved === 'number' && typeof total === 'number' && total > 0)
                  ? Math.max(0, Math.min(1, saved / total))
                  : data.progress;
                return {
                  contentSaved: typeof saved === 'number' ? saved : state.contentSaved,
                  contentStage: { status: data.status, detail: data.detail, progress },
                };
              });
            }
        });
        
        es.addEventListener('log', (ev: MessageEvent) => {
            const rawData = typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data);
            let line = rawData;
            try {
              const parsed = JSON.parse(rawData) as { line?: string };
              line = parsed.line ?? rawData;
            } catch {
              // Keep raw string
            }
            set((prev) => ({ logs: [...prev.logs.slice(-500), line] }));
        });

        es.addEventListener('end', async (ev: MessageEvent) => {
            es.close();
            contentEvtSrc = null;
            const data = JSON.parse(ev.data);
            if (data?.status === 'success') {
                const r = await fetch(`/api/content/result?jobId=${encodeURIComponent(jobId)}`, { cache: 'no-store' });
                if (r.ok) {
                    const result = (await r.json()) as ContentResultPayload;
                    set({ contentResult: result, stage: 'content_ready', isSubscribing: false });
                } else {
                    set({ stage: 'outline_ready', isSubscribing: false });
                }
            } else {
                set({ stage: 'outline_ready', isSubscribing: false });
            }
        });

        // 允许 EventSource 自动重连
        es.onerror = () => {
          // no-op; keep subscribing state to allow auto-reconnect
        };
    },

      startContentGeneration: async () => {
        const { jobId, outlineResult } = get();
        if (!jobId) return;

        // Estimate total points from outline sections
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
          const res = await fetch('/api/content/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refJobId: jobId, debug: true }),
          });

          if (!res.ok) {
            let message = `Failed to start content generation: ${res.status}`;
            try {
              const data = await res.json();
              message = String((data as { detail?: string; error?: string })?.detail ?? (data as { error?: string })?.error ?? message);
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
          await fetch(`/api/content/cancel?jobId=${encodeURIComponent(contentJobId)}`, { method: 'POST' });
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
          await fetch(`/api/outline/cancel?jobId=${encodeURIComponent(jobId)}`, { method: 'POST' });
        } catch {}
        if (outlineEvtSrc) {
          outlineEvtSrc.close();
          outlineEvtSrc = null;
        }
        set({ stage: 'idle', isSubscribing: false });
      },
      
      loadCourse: () => {
        const { contentResult, outlineResult } = get();
        try {
            const pub: string | undefined = contentResult?.publishDir;
            const getSlug = () => {
              if (pub) {
                const parts = String(pub).split(/[\/]+/);
                const ix = parts.lastIndexOf('content');
                if (ix >= 0 && ix + 1 < parts.length) return parts[ix + 1];
              }
              return (
                outlineResult?.reconstructed_outline?.meta?.topic_slug ||
                outlineResult?.subject_slug || ''
              );
            };
            const slug = getSlug();
            if (slug) {
              useLearningStore.getState().loadPath(slug);
            }
          } catch {}
      },

      reset: () => {
        if (outlineEvtSrc) outlineEvtSrc.close();
        if (contentEvtSrc) contentEvtSrc.close();
        outlineEvtSrc = null;
        contentEvtSrc = null;
        set(initialState);
      },
      
      rehydrate: () => {
        const state = get();
        // 优先恢复内容生成（若在阶段4中）
        if (state.contentJobId && !state.contentResult) {
          console.log('Rehydrating content subscription for job:', state.contentJobId);
          if (state.stage === 'idle') set({ stage: 'generating_content' });
          get().subscribeToContent(state.contentJobId);
          return;
        }
        // 其次恢复大纲生成（阶段2/3之间）
        if (state.jobId && !state.outlineResult) {
          console.log('Rehydrating outline subscription for job:', state.jobId);
          if (state.stage === 'idle') set({ stage: 'generating_outline' });
          get().subscribeToOutline(state.jobId);
        }
      }
    }),
    {
      name: 'theme-generator-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) =>
        Object.fromEntries(
          Object.entries(state).filter(([key]) => !['logs', 'showLogs', 'isSubscribing', 'collectStage', 'outlineStage', 'contentStage', 'uiOpen'].includes(key))
        ),
      onRehydrateStorage: () => {
        return (draft, error) => {
          if (error) console.error('Failed to rehydrate theme generator state', error);
          if (draft) {
            draft.rehydrate();
          }
        }
      }
    }
  )
);

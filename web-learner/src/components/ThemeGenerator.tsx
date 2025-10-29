"use client";

import { useEffect, useId, useMemo, Suspense, useState, createElement } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Sparkles, NotebookPen, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useThemeGeneratorStore, GenerationStage } from "@/store/themeGeneratorStore";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type OutlineRenderableSection = string | { id?: string; title?: string };

type OutlineRenderableGroup = {
  id?: string;
  title?: string;
  sections?: OutlineRenderableSection[];
};

const normalizeTextField = (
  source: Record<string, unknown>,
  keys: string[],
): string | undefined => {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    if (typeof value === 'number') {
      return String(value);
    }
  }
  return undefined;
};

const normalizeSection = (
  section: unknown,
  groupIndex: number,
  sectionIndex: number,
): OutlineRenderableSection => {
  const fallbackTitle = `节 ${groupIndex + 1}.${sectionIndex + 1}`;
  const fallbackId = `g${groupIndex}-s${sectionIndex}`;
  if (typeof section === 'string') {
    return { id: fallbackId, title: section };
  }
  if (section && typeof section === 'object') {
    const record = section as Record<string, unknown>;
    const title =
      normalizeTextField(record, ['title', 'section_title', 'topic_title', 'name', 'heading']) ||
      fallbackTitle;
    const id =
      normalizeTextField(record, ['id', 'section_id', 'slug', 'section_slug']) ||
      fallbackId;
    return { id, title };
  }
  return { id: fallbackId, title: fallbackTitle };
};

const normalizeGroup = (group: unknown, groupIndex: number): OutlineRenderableGroup => {
  const fallbackTitle = `第${groupIndex + 1}章`;
  const fallbackId = `g${groupIndex}`;
  if (typeof group === 'string') {
    return { id: fallbackId, title: group };
  }
  if (group && typeof group === 'object') {
    const record = group as Record<string, unknown>;
    const title =
      normalizeTextField(record, ['title', 'group_title', 'chapter_title', 'chapter', 'name']) ||
      fallbackTitle;
    const id =
      normalizeTextField(record, ['id', 'group_id', 'slug', 'group_slug']) ||
      fallbackId;
    const sectionsRaw = Array.isArray(record.sections) ? record.sections : [];
    const sections = sectionsRaw.map((section, sectionIndex) =>
      normalizeSection(section, groupIndex, sectionIndex),
    );
    return { id, title, sections };
  }
  return { id: fallbackId, title: fallbackTitle };
};

const normalizeOutlineGroups = (outline: unknown): OutlineRenderableGroup[] => {
  if (!outline || typeof outline !== 'object') {
    return [];
  }

  const record = outline as Record<string, unknown>;
  const groups = Array.isArray(record.groups) ? record.groups : null;
  const chapters = Array.isArray(record.chapters) ? record.chapters : null;
  const sections = Array.isArray(record.sections) ? record.sections : null;

  if (groups && groups.length > 0) {
    return groups.map((group, index) => normalizeGroup(group, index));
  }

  if (chapters && chapters.length > 0) {
    return chapters.map((group, index) => normalizeGroup(group, index));
  }

  if (sections && sections.length > 0) {
    const outlineTitle = normalizeTextField(record, ['title', 'name']) || '目录';
    let outlineId = outlineTitle;
    const meta = record.meta;
    if (meta && typeof meta === 'object') {
      const metaId = normalizeTextField(meta as Record<string, unknown>, ['topic_slug', 'subject_slug']);
      if (metaId) {
        outlineId = metaId;
      }
    }
    return [
      {
        id: outlineId,
        title: outlineTitle,
        sections: sections.map((section, index) => normalizeSection(section, 0, index)),
      },
    ];
  }

  return [];
};

// Rehydrate on initial load
let rehydrated = false;

export function ThemeGenerator() {
  const stage = useThemeGeneratorStore((state) => state.stage);
  const uiOpen = useThemeGeneratorStore((state) => state.uiOpen);
  const setUiOpen = useThemeGeneratorStore((state) => state.setUiOpen);

  // 自动在进入非 idle 阶段时打开弹层，但不在用户手动关闭后强制打开
  useEffect(() => {
    if (stage !== 'idle') {
      setUiOpen(true);
    }
  }, [stage, setUiOpen]);

  useEffect(() => {
    if (!rehydrated) {
      rehydrated = true;
      useThemeGeneratorStore.getState().rehydrate();
    }
  }, []);

  const reactId = useId();
  const { gradientId, gradientClass } = useMemo(() => {
    const safe = reactId.replace(/[^a-zA-Z0-9_-]/g, "");
    return {
      gradientId: `sparkles-gemini-${safe}`,
      gradientClass: `sparkles-grad-${safe}`,
    };
  }, [reactId]);

  const renderContent = () => {
    switch (stage) {
      case 'idle':
        return <IdleView />;
      case 'generating_outline':
        return <GeneratingOutlineView />;
      case 'outline_ready':
        return <OutlineReadyView />;
      case 'generating_content':
        return <GeneratingContentView />;
      case 'content_ready':
        return <ContentReadyView />;
      default:
        return null;
    }
  };

  return (
    <TooltipProvider>
      <Popover open={uiOpen} onOpenChange={setUiOpen}> 
        <Tooltip>
          <TooltipTrigger asChild>
            <PopoverTrigger asChild>
              <Button variant="outline" size="icon" className="h-9 w-9">
                <Sparkles className={`h-4 w-4 ${gradientClass}`} />
                <svg width="0" height="0" className="absolute pointer-events-none" aria-hidden>
                  <defs>
                    <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#00A8FF" />
                      <stop offset="55%" stopColor="#7B61FF" />
                      <stop offset="100%" stopColor="#FF5BCD" />
                    </linearGradient>
                  </defs>
                </svg>
                <style>{`.${gradientClass} * { stroke: url(#${gradientId}); }`}</style>
              </Button>
            </PopoverTrigger>
          </TooltipTrigger>
          <TooltipContent>
            <p>生成学习主题</p>
          </TooltipContent>
        </Tooltip>

        <PopoverContent className="w-80 p-5" align="center" side="bottom">
          {renderContent()}
          {createElement(
            Suspense,
            { fallback: null },
            createElement(DebugStageSelectorInternal),
          )}
        </PopoverContent>
      </Popover>
    </TooltipProvider>
  );
}

// --- Debug Component (DEV ONLY) ---

const DebugStageSelectorInternal = () => {
  const searchParams = useSearchParams();
  const { setFormField, setUiOpen } = useThemeGeneratorStore();
  const showDebug = searchParams.get('debug') === 'true';

  if (process.env.NODE_ENV !== 'development' || !showDebug) {
    return null;
  }

  const stages: GenerationStage[] = [
    'idle',
    'generating_outline',
    'outline_ready',
    'generating_content',
    'content_ready',
  ];

  const setStage = (stage: GenerationStage) => {
    setFormField('stage', stage);
    if (stage !== 'idle') {
      setUiOpen(true);
    }

    // Reset fields and provide mock data
    setFormField('logs', []);
    setFormField('outlineResult', null);
    setFormField('contentResult', null);

    if (stage === 'generating_outline') {
      setFormField('collectStage', { status: 'running', detail: '正在分析主题...' });
      setFormField('outlineStage', { status: 'pending', detail: '' });
      setFormField('logs', ['[DEBUG] 切换到 generating_outline 阶段.']);
    } else if (stage === 'outline_ready') {
      setFormField('outlineResult', {
        reconstructed_outline: {
          title: 'React 深入浅出 (模拟)',
          groups: [
            {
              id: 'g1',
              title: '第一章：React 基础',
              sections: [{ id: 's1.1', title: '1.1 JSX 语法' }, { id: 's1.2', title: '1.2 组件与 Props' }],
            },
            {
              id: 'g2',
              title: '第二章：State 与生命周期',
              sections: [{ id: 's2.1', title: '2.1 State 管理' }, { id: 's2.2', title: '2.2 生命周期方法' }],
            },
          ],
        },
      });
    } else if (stage === 'generating_content') {
        setFormField('outlineResult', {
            reconstructed_outline: {
              title: 'React 深入浅出 (模拟)',
              groups: [
                { id: 'g1', title: '第一章：React 基础', sections: [{ id: 's1.1', title: '1.1 JSX 语法' }, { id: 's1.2', title: '1.2 组件与 Props' }] },
                { id: 'g2', title: '第二章：State 与生命周期', sections: [{ id: 's2.1', title: '2.1 State 管理' }, { id: 's2.2', title: '2.2 生命周期方法' }] },
              ],
            },
          });
        setFormField('contentStage', { status: 'running', detail: '1/4 生成中：JSX 语法...' });
        setFormField('logs', ['[DEBUG] 切换到 generating_content 阶段.', '正在为第1章生成内容...']);
    } else if (stage === 'content_ready') {
      setFormField('outlineResult', {
        reconstructed_outline: {
          title: 'React 深入浅出 (模拟)',
          groups: [
            { id: 'g1', title: '第一章：React 基础', sections: [{ id: 's1.1', title: '1.1 JSX 语法' }, { id: 's1.2', title: '1.2 组件与 Props' }] },
            { id: 'g2', title: '第二章：State 与生命周期', sections: [{ id: 's2.1', title: '2.1 State 管理' }, { id: 's2.2', title: '2.2 生命周期方法' }] },
            { id: 'g3', title: '第三章：Hooks', sections: [{ id: 's3.1', title: '3.1 useState' }, { id: 's3.2', title: '3.2 useEffect' }] },
          ],
        },
      });
      setFormField('contentResult', {
        reportPath: '/output/debug/report.md',
        publishedFiles: ['file1.md', 'file2.md', 'file3.md', 'file4.md', 'file5.md', 'file6.md'],
      });
    }
  };

  return (
    <div className="mt-4 border-t pt-3">
      <p className="text-xs font-bold text-muted-foreground">调试面板 (URL?debug=true)</p>
      <div className="grid grid-cols-3 gap-1 mt-2">
        {stages.map((s) => (
          <button
            key={s}
            onClick={() => setStage(s)}
            className="text-[10px] bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-900 dark:text-slate-100 px-1 py-0.5 rounded truncate"
            title={s}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
};

// --- Sub-components for each stage ---

const IdleView = () => {
  const { themeName, generationStyle, content, setFormField, startOutlineGeneration, isSubscribing } = useThemeGeneratorStore();

  return (
    <div className="flex flex-col">
      <h4 className="font-medium text-lg leading-relaxed">生成学习主题</h4>
      <p className="text-xs text-muted-foreground mt-1">输入主题名称与偏好，以生成可供预览的大纲。</p>
      
      <div className="border-t pt-4 mt-4 space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="themeName">主题名称</Label>
          <Input
            id="themeName"
            placeholder="例如：React 深入浅出"
            value={themeName}
            onChange={(e) => setFormField('themeName', e.target.value)}
            className="h-9 text-sm"
          />
        </div>

        <div className="space-y-1.5">
          <Label>内容深度</Label>
          <ToggleGroup
            type="single"
            variant="outline"
            value={generationStyle}
            onValueChange={(value) => {
              if (value) setFormField('generationStyle', value as 'principle' | 'preview');
            }}
            className="grid grid-cols-2 w-full"
          >
            <ToggleGroupItem value="preview" aria-label="深度预习" className="group h-auto px-3 py-2 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
              <div className="flex flex-col items-center gap-y-1">
                <div>深度预习</div>
                <div className="text-xs text-muted-foreground/80 group-data-[state=on]:text-primary-foreground">(更深·初步系统性学习)</div>
              </div>
            </ToggleGroupItem>
            <ToggleGroupItem value="principle" aria-label="原理学习" className="group h-auto px-3 py-2 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
              <div className="flex flex-col items-center gap-y-1">
                <div>原理学习</div>
                <div className="text-xs text-muted-foreground/80 group-data-[state=on]:text-primary-foreground">(更浅·零基础理解原理)</div>
              </div>
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="content">学习期待</Label>
          <Textarea
            id="content"
            placeholder="例如：我希望了解 React 的组件化思想和状态管理机制。"
            value={content}
            onChange={(e) => setFormField('content', e.target.value)}
            className="min-h-[80px] text-sm resize-none"
          />
        </div>

        <div>
          <Button
            onClick={startOutlineGeneration}
            className="w-full h-10"
            disabled={!themeName.trim() || !content.trim() || isSubscribing}
          >
            {isSubscribing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <NotebookPen className="h-4 w-4" />
            )}
            开始生成大纲
          </Button>
        </div>
      </div>
    </div>
  );
};

const GeneratingOutlineView = () => {
  const {
    collectStage,
    outlineStage,
    isSubscribing,
    jobId,
    cancelOutlineGeneration, // Assumed to be created in the store
    reset,
    setUiOpen,
  } = useThemeGeneratorStore();

  const [progress, setProgress] = useState(0);

  const failed = collectStage.status === 'error' || outlineStage.status === 'error';
  
  const detailText = failed
    ? (collectStage.detail || outlineStage.detail || '生成已中止')
    : ((collectStage.status !== 'completed' && collectStage.status !== 'error') 
        ? (collectStage.detail || '') 
        : (outlineStage.detail || ''));

  const currentStage = (collectStage.status !== 'completed' && collectStage.status !== 'error') ? '搜集参考教材' : '整合生成大纲';

  // Deterministic progress based on backend numbers + smooth ramp during outline
  useEffect(() => {
    if (failed) {
      setProgress(0);
      return;
    }

    if (outlineStage.status === 'completed') {
      setProgress(100);
      return;
    }

    // Base target from collect stage numeric progress
    let target = 0;
    if (collectStage.status === 'running') {
      const p = typeof collectStage.progress === 'number' ? collectStage.progress : undefined;
      if (typeof p === 'number' && p >= 0) {
        target = Math.max(0, Math.min(50, p * 50));
      } else {
        target = Math.max(target, 1); // minimal visible progress once started
      }
    } else if (collectStage.status === 'completed') {
      target = 50;
    }

    // During outline running, keep increasing slowly up to 90 without falling back
    if (outlineStage.status === 'running') {
      target = Math.max(target, 55);
    }

    setProgress(prev => Math.max(prev, target));
  }, [collectStage.status, collectStage.progress, outlineStage.status, failed]);

  // Smooth ramp while outline is running
  useEffect(() => {
    if (failed) return;
    if (outlineStage.status !== 'running') return;
    const interval = setInterval(() => {
      setProgress(prev => (prev < 90 ? prev + 0.2 : prev));
    }, 200);
    return () => clearInterval(interval);
  }, [outlineStage.status, failed]);


  if (failed) {
    return (
      <div className="space-y-3">
        <h4 className="font-medium text-lg leading-relaxed">生成中止</h4>
        <div className="border-t pt-3 mt-3 space-y-3 text-center">
          <p className="text-sm text-muted-foreground">{detailText}</p>
          <div className="flex gap-2 justify-center pt-2">
            <Button variant="outline" className="h-8 text-xs" onClick={() => setUiOpen(false)}>关闭</Button>
            <Button className="h-8 text-xs" onClick={reset}>重新生成</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-lg leading-relaxed">大纲生成进度</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        <div className="space-y-2">
          <div className="text-sm">
            <div>当前阶段：{currentStage}</div>
            {!!detailText && (
              <div className="text-[11px] text-muted-foreground mt-0.5">{detailText}</div>
            )}
          </div>
          <Progress value={progress} className="h-2 w-full" />
        </div>
        <div className="flex items-center justify-between">
          <LogViewToggle />
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground w-10 text-right">{`${Math.round(progress)}%`}</span>
            {(isSubscribing && jobId) && (
              <Button
                variant="destructive"
                className="h-7 px-3 text-xs font-semibold shadow-sm hover:shadow-md hover:brightness-110 hover:-translate-y-0.5 active:translate-y-0 focus-visible:ring-destructive/30"
                onClick={cancelOutlineGeneration}
              >中止</Button>
            )}
          </div>
        </div>
        <LogView />
      </div>
    </div>
  );
};

const OutlineReadyView = () => {
  const { outlineResult, startContentGeneration, reset } = useThemeGeneratorStore();

  const outline = outlineResult?.reconstructed_outline ?? null;
  const groups: OutlineRenderableGroup[] = normalizeOutlineGroups(outline);
  const title = outline?.title || '生成目录';

  return (
    <div className="flex flex-col">
      <h4 className="font-medium text-lg leading-relaxed">大纲已生成</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        {groups.length > 0 && (
          <div className="border rounded bg-muted/40">
            <div className="px-2 py-1.5 text-xs font-medium border-b">{title} · 目录预览</div>
            <div className="max-h-56 overflow-auto p-2">
              {groups.map((group, groupIndex) => (
                <div key={group?.id || groupIndex} className="mb-2 last:mb-0">
                  <div className="text-xs font-medium leading-snug">{group?.title || `第${groupIndex + 1}章`}</div>
                  <ul className="mt-1 pl-4 list-disc space-y-0.5">
                    {Array.isArray(group?.sections) && group.sections.map((section, sectionIndex) => (
                      <li key={typeof section === 'string' ? sectionIndex : section?.id || sectionIndex} className="text-[11px] leading-tight">
                        {typeof section === 'string' ? section : (section?.title || `节 ${groupIndex + 1}.${sectionIndex + 1}`)}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="flex gap-2 justify-between">
          <Button
            variant="outline"
            className="h-8 text-xs"
            onClick={reset}
          >放弃当前大纲</Button>
          <Button
            className="h-8 text-xs"
            onClick={startContentGeneration}
          >基于此大纲生成知识点</Button>
        </div>
      </div>
    </div>
  );
};

const GeneratingContentView = () => {
  const { contentStage, isSubscribing, contentJobId, cancelContentGeneration, contentTotal } = useThemeGeneratorStore();
  const isGenerating = isSubscribing;

  const failed = contentStage.status === 'error';

  const progressValue = useMemo(() => {
    if (contentStage.status === 'error') return 0;
    if (contentStage.status === 'completed') return 100;

    // Prefer numeric stage progress from store
    if (typeof contentStage.progress === 'number') {
      return Math.max(0, Math.min(100, contentStage.progress * 100));
    }

    // Fallback: parse "已保存 N 个" and divide by estimated total
    const mSaved = typeof contentStage.detail === 'string' ? contentStage.detail.match(/已保存\s*(\d+)\s*个/) : null;
    if (mSaved && contentTotal && contentTotal > 0) {
      const saved = parseInt(mSaved[1], 10);
      return Math.max(0, Math.min(100, (saved / contentTotal) * 100));
    }

    // Last resort: parse x/y pattern
    const detail = contentStage.detail || '';
    const match = detail.match(/(\d+)\/(\d+)/);
    if (match) {
      const current = parseInt(match[1], 10);
      const total = parseInt(match[2], 10);
      if (total > 0) return (current / total) * 100;
    }

    // Indeterminate states
    if (contentStage.status === 'pending') return 1;
    if (contentStage.status === 'running') return 1;
    return 0;
  }, [contentStage, contentTotal]);

  const phaseLabel = useMemo(() => {
    if (failed) return '出错/取消';
    if (contentStage.status === 'completed') return '发布完成';
    if (contentStage.status === 'pending') return '准备生成';
    const detail = String(contentStage.detail || '');
    if (/审核/.test(detail)) return '审核生成内容';
    if (/发布/.test(detail)) return '发布内容';
    if (/初稿/.test(detail)) return '生成初稿';
    return '生成初稿';
  }, [contentStage, failed]);

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-lg leading-relaxed">知识点生成进度</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        <div className="space-y-2">
          <div className="text-sm">
              <div>当前阶段：{phaseLabel}</div>
              {!!contentStage.detail && <div className="text-[11px] text-muted-foreground mt-0.5">{contentStage.detail}</div>}
          </div>
          {!failed && (
              <Progress value={progressValue} className="h-2 w-full" />
          )}
        </div>
        <div className="flex items-center justify-between">
          <LogViewToggle />
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-10 text-right">{`${Math.round(progressValue)}%`}</span>
            {(isGenerating && contentJobId) && (
              <Button
                variant="destructive"
                className="h-7 px-3 text-xs font-semibold shadow-sm hover:shadow-md hover:brightness-110 hover:-translate-y-0.5 active:translate-y-0 focus-visible:ring-destructive/30"
                onClick={cancelContentGeneration}
              >中止</Button>
            )}
          </div>
        </div>
        <LogView />
      </div>
    </div>
  );
};

const ContentReadyView = () => {
  const { contentResult, outlineResult, themeName, loadCourse, setFormField, setUiOpen } = useThemeGeneratorStore();

  const title = outlineResult?.reconstructed_outline?.title || themeName || '新主题';
  const chapterCount = outlineResult?.reconstructed_outline?.groups?.length || 0;
  const pointCount = contentResult?.publishedFiles?.length || 0;

  return (
    <div className="space-y-3">
      <div className="text-lg leading-relaxed font-medium">知识点生成完成 🎉</div>

      {/* New Summary Section */}
      <div className="text-sm text-muted-foreground space-y-1 border-t pt-3 mt-3">
        <div>
          <span className="font-semibold">生成内容：</span>
          <span className="text-foreground">{title}</span>
        </div>
        {chapterCount > 0 && pointCount > 0 && (
          <div>
            <span className="font-semibold">包含：</span>
            <span className="text-foreground">{chapterCount} 章, {pointCount} 个知识点</span>
          </div>
        )}
      </div>
      
      <div className="flex gap-5 pt-2">
        <Button variant="outline" className="h-7 px-2 text-xs" onClick={() => { setFormField('stage', 'idle'); setUiOpen(false); }}>再生成一个知识点</Button>
        <Button
          className="h-7 px-2 text-xs"
          onClick={() => {
            loadCourse();
            setFormField('stage', 'idle');
            setUiOpen(false);
          }}
        >现在开始学习！</Button>
      </div>
    </div>
  );
};

const LogViewToggle = () => {
    const { showLogs, setFormField } = useThemeGeneratorStore();
    return (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs inline-flex items-center gap-1 justify-start pl-0 pr-2"
          onClick={() => setFormField('showLogs', !showLogs)}
        >
          <ChevronRight className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ${showLogs ? 'rotate-90' : 'rotate-0'}`} />
          {showLogs ? '收起日志' : '展开日志'}
        </Button>
    );
}

const LogView = () => {
    const { showLogs, logs } = useThemeGeneratorStore();
    if (!showLogs) return null;
    return (
        <pre className="bg-muted/50 rounded p-2 max-h-48 overflow-auto text-[11px] leading-tight whitespace-pre-wrap">
            {logs.slice(-200).join('\n')}
        </pre>
    );
}

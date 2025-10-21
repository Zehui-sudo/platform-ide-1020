"use client";

import { useEffect, useId, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Sparkles, NotebookPen } from "lucide-react";
import { cn } from "@/lib/utils";
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

// Rehydrate on initial load
let rehydrated = false;

export function ThemeGenerator() {
  const store = useThemeGeneratorStore();
  const { 
    stage, themeName, generationStyle, content, 
    jobId, contentJobId, outlineResult, contentResult,
    logs, showLogs, isSubscribing,
    collectStage, outlineStage, contentStage,
    setFormField, startOutlineGeneration, startContentGeneration,
    cancelContentGeneration, loadCourse, reset,
    uiOpen, setUiOpen,
  } = store;

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

  const isGenerating = stage === 'generating_outline' || stage === 'generating_content' || isSubscribing;

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

        <PopoverContent className="w-80 p-4" align="center" side="bottom">
          {renderContent()}
          <DebugStageSelector />
        </PopoverContent>
      </Popover>
    </TooltipProvider>
  );
}

// --- Debug Component (DEV ONLY) ---

const DebugStageSelectorInternal = () => {
  const searchParams = useSearchParams();
  const showDebug = searchParams.get('debug') === 'true';

  if (process.env.NODE_ENV !== 'development' || !showDebug) {
    return null;
  }

  const { setFormField, setUiOpen } = useThemeGeneratorStore();

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
      setFormField('collectStage', { status: 'processing', detail: '正在分析主题...' });
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
        setFormField('contentStage', { status: 'processing', detail: '1/4 生成中：JSX 语法...' });
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

const DebugStageSelector = () => {
  // Wrap in Suspense as useSearchParams is used internally
  return (
    <Suspense fallback={null}>
      <DebugStageSelectorInternal />
    </Suspense>
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
          <Label>学习风格</Label>
          <ToggleGroup
            type="single"
            variant="outline"
            value={generationStyle}
            onValueChange={(value) => {
              if (value) setFormField('generationStyle', value as 'principle' | 'preview');
            }}
          >
            <ToggleGroupItem value="principle" aria-label="原理学习" className="h-9 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
              原理学习
            </ToggleGroupItem>
            <ToggleGroupItem value="preview" aria-label="深度预习" className="h-9 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
              深度预习
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="content">具体要求</Label>
          <Textarea
            id="content"
            placeholder="可以描述希望包含的具体知识点、希望达到的学习深度等..."
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
  const { collectStage, outlineStage } = useThemeGeneratorStore();

  const currentStage = (collectStage.status !== 'completed' && collectStage.status !== 'error') ? '搜集参考教材' : '整合生成大纲';
  const detail = (currentStage === '搜集参考教材') ? (collectStage.detail || '') : (outlineStage.detail || '');
  const failed = (collectStage.status === 'error' || outlineStage.status === 'error');

  const progressValue = useMemo(() => {
    if (failed) return 0;
    if (collectStage.status !== 'completed' && collectStage.status !== 'error') {
      return 33;
    }
    if (outlineStage.status !== 'completed' && outlineStage.status !== 'error') {
      return 66;
    }
    return 100;
  }, [collectStage.status, outlineStage.status, failed]);

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-lg leading-relaxed">生成进度</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        <div className="space-y-2">
          <div className="text-xs">
            <div>当前阶段：{failed ? '出错' : currentStage}</div>
            {!!detail && !failed && (
              <div className="text-[11px] text-muted-foreground mt-0.5">{detail}</div>
            )}
          </div>
          {!failed && (
            <Progress value={progressValue} className="h-2 w-full" />
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">日志</div>
          <LogViewToggle />
        </div>
        <LogView />
      </div>
    </div>
  );
};

const OutlineReadyView = () => {
  const { outlineResult, startContentGeneration, reset } = useThemeGeneratorStore();

  const outline = outlineResult?.reconstructed_outline || null;
  let groups: any[] = [];
  if (Array.isArray(outline?.groups)) groups = outline.groups;
  else if (Array.isArray(outline?.chapters)) groups = outline.chapters;
  else if (Array.isArray(outline?.sections)) groups = [{ title: outline?.title || '目录', sections: outline.sections }];
  const title = outline?.title || '生成目录';

  return (
    <div className="flex flex-col">
      <h4 className="font-medium text-lg leading-relaxed center">大纲已生成</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        {groups.length > 0 && (
          <div className="border rounded bg-muted/40">
            <div className="px-2 py-1.5 text-xs font-medium border-b">{title} · 目录预览</div>
            <div className="max-h-56 overflow-auto p-2">
              {groups.map((g: any, gi: number) => (
                <div key={g?.id || gi} className="mb-2 last:mb-0">
                  <div className="text-xs font-medium leading-snug">{g?.title || `第${gi + 1}章`}</div>
                  <ul className="mt-1 pl-4 list-disc space-y-0.5">
                    {Array.isArray(g?.sections) && g.sections.map((s: any, si: number) => (
                      <li key={s?.id || si} className="text-[11px] leading-tight">
                        {typeof s === 'string' ? s : (s?.title || `节 ${gi + 1}.${si + 1}`)}
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
          >放弃并重新生成</Button>
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
  const { contentStage, isSubscribing, contentJobId, cancelContentGeneration } = useThemeGeneratorStore();
  const isGenerating = isSubscribing;

  const progressValue = useMemo(() => {
    if (contentStage.status === 'error') return 0;
    if (contentStage.status === 'completed') return 100;

    const detail = contentStage.detail || '';
    const match = detail.match(/(\d+)\/(\d+)/);

    if (match) {
      const current = parseInt(match[1], 10);
      const total = parseInt(match[2], 10);
      if (total > 0) {
        return (current / total) * 100;
      }
    }
    
    if (contentStage.status === 'processing') {
        return 50; // Indeterminate fallback
    }
    if (contentStage.status === 'pending') {
        return 5; // Small progress for pending
    }

    return 0;
  }, [contentStage]);

  const failed = contentStage.status === 'error';

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-lg leading-relaxed">生成知识点</h4>
      <div className="border-t pt-3 mt-3 space-y-3">
        <div className="space-y-2">
          <div className="text-xs">
              <div>状态：{contentStage.status === 'completed' ? '完成' : (failed ? '出错/取消' : '进行中')}</div>
              {!!contentStage.detail && <div className="text-[11px] text-muted-foreground mt-0.5">{contentStage.detail}</div>}
          </div>
          {!failed && (
              <Progress value={progressValue} className="h-2 w-full" />
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">日志</div>
          <div className="flex items-center gap-2">
            {(isGenerating && contentJobId) && (
              <Button
                variant="destructive"
                className="h-7 px-2 text-xs"
                onClick={cancelContentGeneration}
              >中止</Button>
            )}
            <LogViewToggle />
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
      <div className="text-lg leading-relaxed font-medium">知识点生成完成！</div>

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
        <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setFormField('showLogs', !showLogs)}>{showLogs ? '收起' : '展开'}</Button>
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

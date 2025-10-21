"use client";

import { useEffect, useId, useMemo } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
        </PopoverContent>
      </Popover>
    </TooltipProvider>
  );
}

// --- Sub-components for each stage ---

const IdleView = () => {
  const { themeName, generationStyle, content, setFormField, startOutlineGeneration, isSubscribing } = useThemeGeneratorStore();
  const isGenerating = isSubscribing;

  return (
    <div className="flex flex-col space-y-3">
      <h4 className="font-medium text-lg leading-relaxed">生成学习主题</h4>
      <p className="text-xs text-muted-foreground">输入主题名称与偏好，先生成可预览的大纲</p>
      <div className="space-y-2">
        <Input
          placeholder="主题名称（如：React 深入浅出）"
          value={themeName}
          onChange={(e) => setFormField('themeName', e.target.value)}
          className="h-8 text-sm"
        />
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant={generationStyle === 'principle' ? 'default' : 'outline'}
            onClick={() => setFormField('generationStyle', 'principle')}
            className={cn("h-8 text-xs", generationStyle === 'principle' && "bg-primary")}
          >原理学习</Button>
          <Button
            variant={generationStyle === 'preview' ? 'default' : 'outline'}
            onClick={() => setFormField('generationStyle', 'preview')}
            className={cn("h-8 text-xs", generationStyle === 'preview' && "bg-primary")}
          >深度预习</Button>
        </div>
        <Textarea
          placeholder="描述想学习的内容..."
          value={content}
          onChange={(e) => setFormField('content', e.target.value)}
          className="min-h-[60px] text-sm resize-none"
        />
      </div>
      <div className="flex">
        <Button
          variant="outline"
          onClick={startOutlineGeneration}
          className="flex-1 h-8 text-sm hover:bg-primary hover:text-primary-foreground"
          disabled={!themeName.trim() || !content.trim() || isGenerating}
        >开始生成大纲</Button>
      </div>
    </div>
  );
};

const GeneratingOutlineView = () => {
  const { logs, showLogs, setFormField, collectStage, outlineStage, isSubscribing } = useThemeGeneratorStore();
  const isGenerating = isSubscribing;

  const currentStage = (collectStage.status !== 'completed' && collectStage.status !== 'error') ? '搜集参考教材' : '整合生成大纲';
  const detail = (currentStage === '搜集参考教材') ? (collectStage.detail || '') : (outlineStage.detail || '');
  const failed = (collectStage.status === 'error' || outlineStage.status === 'error');

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-sm leading-none">生成进度</h4>
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs">
          {!failed && (<Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />)}
          <div>
            <div>当前阶段：{failed ? '出错' : currentStage}</div>
            {!!detail && !failed && (
              <div className="text-[11px] text-muted-foreground mt-0.5">{detail}</div>
            )}
          </div>
        </div>
      </div>
      <LogView />
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
    <div className="flex flex-col space-y-3">
      <h4 className="font-bold text-lg leading-relaxed center">大纲已生成</h4>
      {groups.length > 0 && (
        <div className="mt-1.5 border rounded bg-muted/40">
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
      <div className="flex gap-2">
        <Button
          className="h-8 text-xs"
          onClick={startContentGeneration}
        >基于此大纲生成知识点</Button>
        <Button
          variant="outline"
          className="h-8 text-xs"
          onClick={reset}
        >放弃并重新生成</Button>
      </div>
    </div>
  );
};

const GeneratingContentView = () => {
  const { contentStage, isSubscribing, contentJobId, cancelContentGeneration } = useThemeGeneratorStore();
  const isGenerating = isSubscribing;

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-sm leading-none">生成知识点（章节内容）</h4>
      <div className="flex items-center gap-2 text-xs">
        {(isGenerating && contentStage.status !== 'error') && (<Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />)}
        <div>
          <div>状态：{contentStage.status === 'completed' ? '完成' : (contentStage.status === 'error' ? '出错/取消' : '进行中')}</div>
          {!!contentStage.detail && <div className="text-[11px] text-muted-foreground mt-0.5">{contentStage.detail}</div>}
        </div>
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
  );
};

const ContentReadyView = () => {
  const { contentResult, loadCourse, setFormField, setUiOpen } = useThemeGeneratorStore();

  return (
    <div className="space-y-3">
      <div className="text-xs">知识点生成完成</div>
      <div className="text-[11px] text-muted-foreground break-words">报告: {contentResult?.reportPath || '—'}</div>
      {Array.isArray(contentResult?.publishedFiles) && contentResult.publishedFiles.length > 0 && (
        <div className="text-[11px] text-muted-foreground">共发布 {contentResult.publishedFiles.length} 个内容文件</div>
      )}
      <div className="flex gap-2">
        <Button
          className="h-7 px-2 text-xs"
          onClick={() => {
            loadCourse();
            setFormField('stage', 'idle');
            setUiOpen(false);
          }}
        >打开学习路径</Button>
        <Button variant="outline" className="h-7 px-2 text-xs" onClick={() => { setFormField('stage', 'idle'); setUiOpen(false); }}>关闭</Button>
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

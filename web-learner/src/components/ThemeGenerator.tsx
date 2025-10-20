"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
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

export function ThemeGenerator() {
  const [isOpen, setIsOpen] = useState(false);
  const [themeName, setThemeName] = useState("");
  const [generationStyle, setGenerationStyle] = useState<'principle' | 'preview'>('principle');
  const [content, setContent] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [stageCollect, setStageCollect] = useState<{status: 'pending'|'running'|'completed'|'error', detail?: string, progress?: number}>({ status: 'pending' });
  const [stageOutline, setStageOutline] = useState<{status: 'pending'|'running'|'completed'|'error', detail?: string}>({ status: 'pending' });
  const [resultOutline, setResultOutline] = useState<any>(null);
  const evtSrcRef = useRef<EventSource | null>(null);
  const reactId = useId();
  const { gradientId, gradientClass } = useMemo(() => {
    const safe = reactId.replace(/[^a-zA-Z0-9_-]/g, "");
    return {
      gradientId: `sparkles-gemini-${safe}`,
      gradientClass: `sparkles-grad-${safe}`,
    };
  }, [reactId]);

  const handleGenerate = async () => {
    if (!themeName.trim()) return;
    // 期望内容可为空，这里沿用你之前逻辑要求非空时才可点击
    if (!content.trim()) return;

    setIsGenerating(true);
    setLogs([]);
    setStageCollect({ status: 'pending' });
    setStageOutline({ status: 'pending' });
    setResultOutline(null);
    setJobId(null);

    try {
      const styleMap: Record<'principle'|'preview', 'principles'|'deep_preview'> = {
        principle: 'principles',
        preview: 'deep_preview',
      };
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
      if (!res.ok) throw new Error(`启动任务失败: ${res.status}`);
      const { jobId } = await res.json();
      setJobId(jobId);

      // 订阅 SSE
      const es = new EventSource(`/api/outline/stream?jobId=${encodeURIComponent(jobId)}`);
      evtSrcRef.current = es;
      es.addEventListener('stage', (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.id === 'collect') {
            setStageCollect({ status: data.status, detail: data.detail, progress: typeof data.progress === 'number' ? Math.max(0, Math.min(1, data.progress)) : undefined });
          } else if (data?.id === 'outline') {
            setStageOutline({ status: data.status, detail: data.detail });
          }
        } catch {}
      });
      es.addEventListener('log', (ev: MessageEvent) => {
        const line = (() => {
          try { const obj = JSON.parse(ev.data); return obj?.line ?? String(ev.data); } catch { return String(ev.data); }
        })();
        setLogs(prev => (prev.length > 500 ? prev.slice(prev.length - 500) : prev).concat([line]));
      });
      es.addEventListener('file', (ev: MessageEvent) => {
        // 可选：展示 outPath/logPath
      });
      es.addEventListener('end', async (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.status === 'success' && jobId) {
            const r = await fetch(`/api/outline/result?jobId=${encodeURIComponent(jobId)}`, { cache: 'no-store' });
            if (r.ok) {
              const json = await r.json();
              setResultOutline(json);
            }
          }
        } catch {}
        setIsGenerating(false);
        try { es.close(); } catch {}
        evtSrcRef.current = null;
      });
      es.onerror = () => {
        setIsGenerating(false);
        try { es.close(); } catch {}
        evtSrcRef.current = null;
      };
    } catch (error) {
      console.error('生成主题失败:', error);
      setIsGenerating(false);
    }
  };

  useEffect(() => () => {
    if (evtSrcRef.current) {
      try { evtSrcRef.current.close(); } catch {}
      evtSrcRef.current = null;
    }
  }, []);

  return (
    <TooltipProvider>
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <Tooltip>
          <TooltipTrigger asChild>
            <PopoverTrigger asChild>
              <Button variant="outline" size="icon" className="h-9 w-9">
                {/* Keep original Lucide icon, override stroke via CSS to use gradient */}
                <Sparkles className={`h-4 w-4 ${gradientClass}`} />
                {/* Local gradient definition (hidden) */}
                <svg width="0" height="0" className="absolute pointer-events-none" aria-hidden>
                  <defs>
                    <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#00A8FF" />
                      <stop offset="55%" stopColor="#7B61FF" />
                      <stop offset="100%" stopColor="#FF5BCD" />
                    </linearGradient>
                  </defs>
                </svg>
                {/* Scoped CSS: apply gradient stroke to paths within the icon */}
                <style>{`.${gradientClass} * { stroke: url(#${gradientId}); }`}</style>
              </Button>
            </PopoverTrigger>
          </TooltipTrigger>
          <TooltipContent>
            <p>生成学习主题</p>
          </TooltipContent>
        </Tooltip>

        <PopoverContent className="w-[380px] p-4" align="center" side="bottom">
          {!isGenerating && !jobId && !resultOutline && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm leading-none">生成学习主题</h4>
              <p className="text-xs text-muted-foreground">输入主题名称与偏好，先生成可预览的大纲</p>
              <div className="space-y-2">
                <Input
                  placeholder="主题名称（如：React 深入浅出）"
                  value={themeName}
                  onChange={(e) => setThemeName(e.target.value)}
                  className="h-8 text-sm"
                />
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant={generationStyle === 'principle' ? 'default' : 'outline'}
                    onClick={() => setGenerationStyle('principle')}
                    className={cn("h-8 text-xs", generationStyle === 'principle' && "bg-primary/80 hover:bg-primary/70")}
                  >原理学习</Button>
                  <Button
                    variant={generationStyle === 'preview' ? 'default' : 'outline'}
                    onClick={() => setGenerationStyle('preview')}
                    className={cn("h-8 text-xs", generationStyle === 'preview' && "bg-primary/80 hover:bg-primary/70")}
                  >深度预习</Button>
                </div>
                <Textarea
                  placeholder="描述想学习的内容..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="min-h-[60px] text-sm resize-none"
                />
              </div>
              <div className="flex">
                <Button
                  variant="outline"
                  onClick={handleGenerate}
                  className="flex-1 h-8 text-sm hover:bg-primary/90 hover:text-primary-foreground"
                  disabled={!themeName.trim() || !content.trim() || isGenerating}
                >开始生成大纲</Button>
              </div>
            </div>
          )}

          {(isGenerating || jobId) && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm leading-none">生成进度</h4>
              <div className="space-y-2">
                {(() => {
                  // 计算当前阶段与提示
                  const currentStage = (stageCollect.status !== 'completed' && stageCollect.status !== 'error') ? '搜集参考教材' : '整合生成大纲';
                  const detail = (currentStage === '搜集参考教材') ? (stageCollect.detail || '') : (stageOutline.detail || '');
                  const ended = (!isGenerating && resultOutline);
                  const failed = (stageCollect.status === 'error' || stageOutline.status === 'error');
                  return (
                    <div className="flex items-center gap-2 text-xs">
                      {(!ended && !failed) && (<Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />)}
                      <div>
                        <div>当前阶段：{ended ? '完成' : (failed ? '出错' : currentStage)}</div>
                        {!!detail && !ended && !failed && (
                          <div className="text-[11px] text-muted-foreground mt-0.5">{detail}</div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">日志</div>
                <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setShowLogs(v => !v)}>{showLogs ? '收起' : '展开'}</Button>
              </div>
              {showLogs && (
                <pre className="bg-muted/50 rounded p-2 max-h-48 overflow-auto text-[11px] leading-tight whitespace-pre-wrap">
{logs.slice(-200).join('\n')}
                </pre>
              )}
              {!isGenerating && resultOutline && (
                <div className="space-y-2">
                  <div className="text-xs">大纲已生成</div>
                  <div className="text-[11px] text-muted-foreground break-words">主题: {resultOutline?.reconstructed_outline?.meta?.subject || themeName}</div>
                  <div className="text-[11px] text-muted-foreground">类型: {resultOutline?.reconstructed_outline?.meta?.subject_type}</div>
                  <div className="flex gap-2">
                    <Button variant="outline" className="h-7 px-2 text-xs" onClick={() => setIsOpen(false)}>关闭</Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </PopoverContent>
      </Popover>
    </TooltipProvider>
  );
}

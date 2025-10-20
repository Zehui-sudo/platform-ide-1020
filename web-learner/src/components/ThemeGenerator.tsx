"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { useLearningStore } from "@/store/learningStore";
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
  // 第四阶段：内容生成
  const [isContentGenerating, setIsContentGenerating] = useState(false);
  const [contentJobId, setContentJobId] = useState<string | null>(null);
  const [contentStage, setContentStage] = useState<{status: 'pending'|'running'|'completed'|'error', detail?: string}>({ status: 'pending' });
  const [contentResult, setContentResult] = useState<any>(null);
  const evtContentRef = useRef<EventSource | null>(null);
  const loadPath = useLearningStore((s) => s.loadPath);

  // --- 本地持久化（避免刷新丢失） ---
  const STATE_KEY = 'theme-gen-state-v1';
  function saveState() {
    try {
      const obj = {
        themeName,
        generationStyle,
        content,
        jobId,
        hasResult: !!resultOutline,
        contentJobId,
      };
      if (typeof window !== 'undefined') localStorage.setItem(STATE_KEY, JSON.stringify(obj));
    } catch {}
  }
  function loadState() {
    try {
      if (typeof window === 'undefined') return null;
      const raw = localStorage.getItem(STATE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch { return null; }
  }
  useEffect(() => { saveState(); }, [themeName, generationStyle, content, jobId, resultOutline, contentJobId]);

  // 统一订阅辅助
  const subscribeOutline = (jid: string) => {
    try {
      const es = new EventSource(`/api/outline/stream?jobId=${encodeURIComponent(jid)}`);
      evtSrcRef.current = es;
      es.addEventListener('hello', (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          const snap = data?.snapshot || {};
          if (snap?.stages) {
            const stc = snap.stages.collect; const sto = snap.stages.outline;
            if (stc) setStageCollect({ status: stc.status, detail: stc.detail, progress: stc.progress });
            if (sto) setStageOutline({ status: sto.status, detail: sto.detail });
          }
          if (snap?.status && snap.status !== 'running') {
            setIsGenerating(false);
          } else {
            setIsGenerating(true);
          }
        } catch {}
      });
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
        const line = (() => { try { const obj = JSON.parse(ev.data); return obj?.line ?? String(ev.data); } catch { return String(ev.data); }})();
        setLogs(prev => (prev.length > 500 ? prev.slice(prev.length - 500) : prev).concat([line]));
      });
      es.addEventListener('file', () => {});
      es.addEventListener('end', async (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.status === 'success' && jid) {
            const r = await fetch(`/api/outline/result?jobId=${encodeURIComponent(jid)}`, { cache: 'no-store' });
            if (r.ok) setResultOutline(await r.json());
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
    } catch {}
  };
  const subscribeContent = (jid: string) => {
    try {
      const es = new EventSource(`/api/content/stream?jobId=${encodeURIComponent(jid)}`);
      evtContentRef.current = es;
      es.addEventListener('hello', (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          const snap = data?.snapshot || {};
          if (snap?.stages?.content) setContentStage({ status: snap.stages.content.status, detail: snap.stages.content.detail });
          if (snap?.status && snap.status !== 'running') setIsContentGenerating(false); else setIsContentGenerating(true);
        } catch {}
      });
      es.addEventListener('stage', (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.id === 'content') setContentStage({ status: data.status, detail: data.detail });
        } catch {}
      });
      es.addEventListener('log', (ev: MessageEvent) => {
        const line = (() => { try { const obj = JSON.parse(ev.data); return obj?.line ?? String(ev.data); } catch { return String(ev.data); }})();
        setLogs(prev => (prev.length > 500 ? prev.slice(prev.length - 500) : prev).concat([line]));
      });
      es.addEventListener('file', () => {});
      es.addEventListener('end', async (ev: MessageEvent) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.status === 'success' && jid) {
            const r = await fetch(`/api/content/result?jobId=${encodeURIComponent(jid)}`, { cache: 'no-store' });
            if (r.ok) setContentResult(await r.json());
          }
        } catch {}
        setIsContentGenerating(false);
        try { es.close(); } catch {}
        evtContentRef.current = null;
      });
      es.onerror = () => {
        setIsContentGenerating(false);
        try { es.close(); } catch {}
        evtContentRef.current = null;
      };
    } catch {}
  };

  // 刷新恢复：根据持久化的 jobId 重新订阅
  useEffect(() => {
    const st = loadState();
    if (!st) return;
    try {
      if (typeof st.themeName === 'string') setThemeName(st.themeName);
      if (st.generationStyle === 'principle' || st.generationStyle === 'preview') setGenerationStyle(st.generationStyle);
      if (typeof st.content === 'string') setContent(st.content);
    } catch {}
    try {
      if (st.jobId && !resultOutline) {
        setJobId(st.jobId);
        setIsGenerating(true);
        subscribeOutline(st.jobId);
      }
    } catch {}
    try {
      if (st.contentJobId) {
        setContentJobId(st.contentJobId);
        setIsContentGenerating(true);
        subscribeContent(st.contentJobId);
      }
    } catch {}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
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
      subscribeOutline(jobId);
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

        <PopoverContent className="w-[420px] p-4" align="center" side="bottom">
          {/* 阶段1：输入表单 */}
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

          {/* 阶段3：结果预览（若进入阶段4，则隐藏） */}
          {!isGenerating && !!resultOutline && !isContentGenerating && !contentJobId && !contentResult && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm leading-none">大纲已生成</h4>
              <div className="text-[11px] text-muted-foreground break-words">主题: {resultOutline?.reconstructed_outline?.meta?.subject || themeName}</div>
              <div className="text-[11px] text-muted-foreground">类型: {resultOutline?.reconstructed_outline?.meta?.subject_type}</div>
              {(() => {
                const outline = resultOutline?.reconstructed_outline || null;
                let groups: any[] = [];
                if (Array.isArray(outline?.groups)) groups = outline.groups;
                else if (Array.isArray(outline?.chapters)) groups = outline.chapters;
                else if (Array.isArray(outline?.sections)) groups = [{ title: outline?.title || '目录', sections: outline.sections }];
                const title = outline?.title || '生成目录';
                if (!groups.length) return null;
                return (
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
                );
              })()}
              <div className="flex gap-2">
                <Button
                  className="h-8 text-xs"
                  onClick={async () => {
                    try {
                      setIsContentGenerating(true);
                      setContentStage({ status: 'running', detail: '启动脚本中…' });
                      setContentResult(null);
                      setLogs([]); // 清空日志，进入阶段4独立日志
                      const res = await fetch('/api/content/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refJobId: jobId }), // 默认全部章节
                      });
                      if (!res.ok) throw new Error(`启动内容生成失败: ${res.status}`);
                      const { jobId: cJobId } = await res.json();
                      setContentJobId(cJobId);
                      const es = new EventSource(`/api/content/stream?jobId=${encodeURIComponent(cJobId)}`);
                      evtContentRef.current = es;
                      es.addEventListener('stage', (ev: MessageEvent) => {
                        try {
                          const data = JSON.parse(ev.data);
                          if (data?.id === 'content') setContentStage({ status: data.status, detail: data.detail });
                        } catch {}
                      });
                      es.addEventListener('log', (ev: MessageEvent) => {
                        const line = (() => { try { const obj = JSON.parse(ev.data); return obj?.line ?? String(ev.data); } catch { return String(ev.data); }})();
                        setLogs(prev => (prev.length > 500 ? prev.slice(prev.length - 500) : prev).concat([line]));
                      });
                      es.addEventListener('file', (ev: MessageEvent) => { /* 可选显示 reportPath/logPath */ });
                      es.addEventListener('end', async (ev: MessageEvent) => {
                        try {
                          const data = JSON.parse(ev.data);
                          if (data?.status === 'success' && cJobId) {
                            const r = await fetch(`/api/content/result?jobId=${encodeURIComponent(cJobId)}`, { cache: 'no-store' });
                            if (r.ok) setContentResult(await r.json());
                          }
                        } catch {}
                        setIsContentGenerating(false);
                        try { es.close(); } catch {}
                        evtContentRef.current = null;
                      });
                      es.onerror = () => {
                        setIsContentGenerating(false);
                        try { es.close(); } catch {}
                        evtContentRef.current = null;
                      };
                    } catch (e) {
                      console.error(e);
                      setIsContentGenerating(false);
                    }
                  }}
                >基于此大纲生成知识点</Button>
                <Button
                  variant="outline"
                  className="h-8 text-xs"
                  onClick={() => {
                    // 复位，回到阶段1
                    setResultOutline(null);
                    setLogs([]);
                    setJobId(null);
                    setIsGenerating(false);
                    setContentJobId(null);
                    setIsContentGenerating(false);
                    setContentStage({ status: 'pending' });
                    setContentResult(null);
                  }}
                >放弃并重新生成</Button>
              </div>
            </div>
          )}

          {/* 阶段2：进度与日志 */}
          {(isGenerating || (!!jobId && !resultOutline)) && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm leading-none">生成进度</h4>
              <div className="space-y-2">
                {(() => {
                  // 计算当前阶段与提示
                  const currentStage = (stageCollect.status !== 'completed' && stageCollect.status !== 'error') ? '搜集参考教材' : '整合生成大纲';
                  const detail = (currentStage === '搜集参考教材') ? (stageCollect.detail || '') : (stageOutline.detail || '');
                  const ended = (!isGenerating && !!resultOutline);
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
            </div>
          )}

          {/* 阶段4：内容生成进度（开始后独占显示） */}
          {((isContentGenerating || contentJobId) && true) && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm leading-none">生成知识点（章节内容）</h4>
              <div className="flex items-center gap-2 text-xs">
                {(isContentGenerating && contentStage.status !== 'error') && (<Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />)}
                <div>
                  <div>状态：{contentStage.status === 'completed' ? '完成' : (contentStage.status === 'error' ? '出错/取消' : '进行中')}</div>
                  {!!contentStage.detail && <div className="text-[11px] text-muted-foreground mt-0.5">{contentStage.detail}</div>}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">日志</div>
                <div className="flex items-center gap-2">
                  {(isContentGenerating && contentJobId) && (
                    <Button
                      variant="destructive"
                      className="h-7 px-2 text-xs"
                      onClick={async () => {
                        try {
                          await fetch(`/api/content/cancel?jobId=${encodeURIComponent(contentJobId!)}`, { method: 'POST' });
                        } catch {}
                        setIsContentGenerating(false);
                        try { evtContentRef.current?.close(); } catch {}
                        evtContentRef.current = null;
                      }}
                    >中止</Button>
                  )}
                  <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setShowLogs(v => !v)}>{showLogs ? '收起' : '展开'}</Button>
                </div>
              </div>
              {showLogs && (
                <pre className="bg-muted/50 rounded p-2 max-h-56 overflow-auto text-[11px] leading-tight whitespace-pre-wrap">
{logs.slice(-200).join('\n')}
                </pre>
              )}
              {!isContentGenerating && contentResult && (
                <div className="space-y-2">
                  <div className="text-xs">知识点生成完成</div>
                  <div className="text-[11px] text-muted-foreground break-words">报告: {contentResult?.reportPath || '—'}</div>
                  {Array.isArray(contentResult?.publishedFiles) && contentResult.publishedFiles.length > 0 && (
                    <div className="text-[11px] text-muted-foreground">共发布 {contentResult.publishedFiles.length} 个内容文件</div>
                  )}
                  <div className="flex gap-2">
                    <Button
                      className="h-7 px-2 text-xs"
                      onClick={() => {
                        try {
                          const pub: string | undefined = contentResult?.publishDir;
                          const getSlug = () => {
                            if (pub) {
                              const parts = String(pub).split(/[\\/]+/);
                              const ix = parts.lastIndexOf('content');
                              if (ix >= 0 && ix + 1 < parts.length) return parts[ix + 1];
                            }
                            return (
                              resultOutline?.reconstructed_outline?.meta?.topic_slug ||
                              resultOutline?.subject_slug || ''
                            );
                          };
                          const slug = getSlug();
                          if (slug) {
                            loadPath(slug);
                            setIsOpen(false);
                          }
                        } catch { setIsOpen(false); }
                      }}
                    >打开学习路径</Button>
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

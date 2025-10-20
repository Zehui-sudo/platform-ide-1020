'use client';

import { useRef, useEffect } from 'react';
import { useLearningStore } from '@/store/learningStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, BookOpen, CheckCircle2, Star } from 'lucide-react';
import { EnhancedMarkdownRenderer } from './EnhancedMarkdownRenderer';
import { InteractiveCodeBlock } from './InteractiveCodeBlock';
import { useTextSelection } from '@/hooks/useTextSelection';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

export function ContentDisplay() {
  const currentSection = useLearningStore((state) => state.currentSection);
  const currentPath = useLearningStore((state) => state.currentPath);
  const loading = useLearningStore((state) => state.loading);
  const error = useLearningStore((state) => state.error);
  const fontSize = useLearningStore((state) => state.fontSize);
  const userProgress = useLearningStore((state) => state.userProgress);
  const toggleSectionComplete = useLearningStore((state) => state.toggleSectionComplete);
  const toggleSectionFavorite = useLearningStore((state) => state.toggleSectionFavorite);
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const currentSectionIdRef = useRef(currentSection?.id);
  const lastSectionIdRef = useRef<string | undefined>(currentSection?.id);
  const bottomReachedRef = useRef(false);
  const debugRef = useRef(false);
  const prevAtBottomRef = useRef(false);
  // 防止在严格模式或重复触发情况下对同一节重复“自动完成”
  const justAutoCompletedRef = useRef<Set<string>>(new Set());

  const BOTTOM_THRESHOLD = 64; // px

  // Enable text selection
  useTextSelection(contentRef as React.RefObject<HTMLElement>);

  // 初始化调试开关：localStorage 设置 learn:debug:auto-complete = '1' 开启
  useEffect(() => {
    try {
      debugRef.current = localStorage.getItem('learn:debug:auto-complete') === '1';
    } catch {}
  }, []);

  // 监听滚动，判断是否触底
  useEffect(() => {
    const viewport = scrollAreaRef.current?.querySelector(
      '[data-radix-scroll-area-viewport], [data-slot="scroll-area-viewport"]'
    ) as HTMLDivElement | null;
    if (!viewport) return;

    const onScroll = () => {
      const atBottom =
        viewport.scrollTop + viewport.clientHeight >=
        viewport.scrollHeight - BOTTOM_THRESHOLD;
      if (atBottom) bottomReachedRef.current = true;
      if (debugRef.current && atBottom && !prevAtBottomRef.current) {
        // 仅在首次到达底部时打印一次
        // 打印当前节和滚动参数，便于诊断
        // eslint-disable-next-line no-console
        console.log('[auto-complete] reached bottom', {
          sectionId: currentSection?.id,
          scrollTop: viewport.scrollTop,
          clientHeight: viewport.clientHeight,
          scrollHeight: viewport.scrollHeight,
        });
      }
      prevAtBottomRef.current = atBottom;
    };

    viewport.addEventListener('scroll', onScroll, { passive: true });
    // 初始化计算一次
    onScroll();
    return () => viewport.removeEventListener('scroll', onScroll);
  }, [currentSection?.id]);

  // 章节切换后，若上个章节已触底且进入了下一个章节，则自动标记为完成
  useEffect(() => {
    const prevId = lastSectionIdRef.current;
    const nextId = currentSection?.id;
    lastSectionIdRef.current = nextId || undefined;

    if (!prevId || !nextId || prevId === nextId || !currentPath) return;
    if (!bottomReachedRef.current) return;

    // 拍平当前路径下的所有节，计算顺序
    const sections = currentPath.chapters.flatMap((ch) =>
      (ch.sections && ch.sections.length > 0)
        ? ch.sections
        : (ch.groups || []).flatMap((g) => g.sections)
    );

    const prevIndex = sections.findIndex((s) => s.id === prevId);
    const nextIndex = sections.findIndex((s) => s.id === nextId);
    if (debugRef.current) {
      // eslint-disable-next-line no-console
      console.log('[auto-complete] section change', { prevId, nextId, prevIndex, nextIndex, bottomBeforeChange: true });
    }
    if (prevIndex >= 0 && nextIndex === prevIndex + 1) {
      // 使用最新 store 状态进行判定，避免闭包中 userProgress 过期
      const freshCompleted = !!useLearningStore.getState().userProgress[prevId]?.isCompleted;
      const justDone = justAutoCompletedRef.current.has(prevId);
      if (!freshCompleted && !justDone) {
        try {
          toggleSectionComplete(prevId);
          justAutoCompletedRef.current.add(prevId);
          // 一段时间后移除标记，避免常驻内存
          setTimeout(() => {
            justAutoCompletedRef.current.delete(prevId);
          }, 4000);
          if (debugRef.current) {
            // eslint-disable-next-line no-console
            console.log('[auto-complete] marked completed', { sectionId: prevId });
          }
        } catch {}
      }
    }

    // 消耗该标记，避免后续误判；并将新章节滚动重置到顶部
    bottomReachedRef.current = false;
    const viewport = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement | null;
    if (viewport) viewport.scrollTop = 0;
    prevAtBottomRef.current = false;
  }, [currentSection?.id, currentPath, toggleSectionComplete, userProgress]);

  if (loading.section) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="space-y-4 w-full max-w-2xl">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-8 w-1/4" />
        </div>
      </div>
    );
  }

  if (error.section) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <Alert variant="destructive" className="max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>加载失败</AlertTitle>
          <AlertDescription>
            {error.section}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!currentSection) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">选择学习内容</h3>
          <p className="text-sm text-muted-foreground">
            请从左侧导航栏选择一个章节开始学习
          </p>
        </div>
      </div>
    );
  }

  const progress = currentSection ? userProgress[currentSection.id] : undefined;
  const isCompleted = progress?.isCompleted || false;
  const isFavorite = progress?.isFavorite || false;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}

      {/* Content */}
      <ScrollArea className="flex-1" ref={scrollAreaRef}>
        <div 
          ref={contentRef}
          className="p-6 pt-0 space-y-6 max-w-4xl mx-auto"
          style={{ 
            fontSize: `${fontSize}px`,
            lineHeight: fontSize >= 18 ? 1.8 : 1.6
          }}>
          {currentSection.contentBlocks.map((block, index) => (
            <div key={`block-${currentSection.id}-${index}`}>
              {block.type === 'markdown' && (
                <div className="max-w-none">
                  <EnhancedMarkdownRenderer 
                    content={block.content}
                    fontSize={fontSize}
                    sectionScopeId={currentSection.id}
                    markdownIndex={index}
                  />
                </div>
              )}
              
              {block.type === 'code' && (
                <div
                  className="my-6"
                  data-role="code-block"
                  data-language={block.language}
                  data-section-id={`${currentSection.id}-code-${index}`}
                  data-markdown-index={index}
                >
                  <InteractiveCodeBlock
                    key={`${currentSection.id}-code-${index}`}
                    language={block.language}
                    initialCode={block.code}
                    sectionId={`${currentSection.id}-code-${index}`}
                    fontSize={fontSize}
                  />
                </div>
              )}
            </div>
          ))}
          
          {currentSection.contentBlocks.length === 0 && (
            <div className="text-center py-8">
              <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">内容准备中</h3>
              <p className="text-sm text-muted-foreground">
                这个章节的内容正在精心准备中，敬请期待��
              </p>
            </div>
          )}
          
          {/* Progress Actions */}
          {currentSection.contentBlocks.length > 0 && (
            <div className="mt-12 space-y-4">
              <Separator />
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
                <div className="flex flex-col sm:flex-row gap-3">
                  <Button
                    variant={isCompleted ? "default" : "outline"}
                    size="lg"
                    onClick={() => toggleSectionComplete(currentSection.id)}
                    className="w-full sm:w-auto"
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    {isCompleted ? '已完成学习' : '标记为已完成'}
                  </Button>
                  
                  <Button
                    variant={isFavorite ? "default" : "outline"}
                    size="lg"
                    onClick={() => toggleSectionFavorite(currentSection.id)}
                    className={`w-full sm:w-auto ${isFavorite ? 'bg-yellow-500 hover:bg-yellow-600' : ''}`}
                  >
                    <Star className={`mr-2 h-4 w-4 ${isFavorite ? 'fill-current' : ''}`} />
                    {isFavorite ? '已收藏' : '添加到收藏'}
                  </Button>
                </div>
                
                {(isCompleted || isFavorite) && (
                  <div className="text-sm text-muted-foreground">
                    {isCompleted && progress?.completedAt && (
                      <p>完成时间: {new Date(progress.completedAt).toLocaleDateString('zh-CN')}</p>
                    )}
                    {isFavorite && progress?.favoritedAt && (
                      <p>收藏时间: {new Date(progress.favoritedAt).toLocaleDateString('zh-CN')}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

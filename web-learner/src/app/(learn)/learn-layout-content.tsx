'use client';

import * as React from 'react';
import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import type { ImperativePanelHandle } from 'react-resizable-panels';
import { LearnNavBar } from '@/components/LearnNavBar';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from '@/components/ui/resizable';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { PanelRightClose, PanelLeftClose, Bot, List } from 'lucide-react';
import { useLearningStore } from '@/store/learningStore';

export default function LearnLayoutContent({ children }: { children?: React.ReactNode }) {
  const loadPath = useLearningStore((state) => state.loadPath);
  const loadSection = useLearningStore((state) => state.loadSection);
  const currentPath = useLearningStore((state) => state.currentPath);
  const uiState = useLearningStore((state) => state.uiState);
  const updateUIState = useLearningStore((state) => state.updateUIState);
  const searchParams = useSearchParams();
  const subjectFromUrl = searchParams.get('subject') ?? searchParams.get('language');
  const sectionFromUrl = searchParams.get('section');

  React.useEffect(() => {
    const currentSubject = currentPath?.subject;

    if (subjectFromUrl && subjectFromUrl !== currentSubject) {
      loadPath(subjectFromUrl);
    } else if (!subjectFromUrl && !currentSubject) {
      const savedSubject = localStorage.getItem('preferred-subject') || localStorage.getItem('preferred-language') || 'python';
      loadPath(savedSubject);
    }

    if (sectionFromUrl) {
      loadSection(sectionFromUrl);
    } else {
      const lastOpened = localStorage.getItem('last-opened-section');
      if (lastOpened) {
        loadSection(lastOpened);
      }
    }
  }, [subjectFromUrl, sectionFromUrl, currentPath, loadPath, loadSection]);

  const navPanelRef = React.useRef<ImperativePanelHandle>(null);
  const aiPanelRef = React.useRef<ImperativePanelHandle>(null);
  const desktopContainerRef = React.useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = React.useState<number>(0);
  const isNavCollapsed = uiState.navCollapsed || false;
  const isAiCollapsed = uiState.aiCollapsed || false;
  const [deferHeavy, setDeferHeavy] = React.useState(false);
  const autoSuppressUntilRef = React.useRef<number>(0);

  const toggleNavSidebar = () => {
    const panel = navPanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
        updateUIState({ navCollapsed: false });
      } else {
        panel.collapse();
        updateUIState({ navCollapsed: true });
      }
    }
    autoSuppressUntilRef.current = Date.now() + 4000;
  };

  const toggleAiSidebar = () => {
    const panel = aiPanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
        updateUIState({ aiCollapsed: false });
      } else {
        panel.collapse();
        updateUIState({ aiCollapsed: true });
      }
    }
    autoSuppressUntilRef.current = Date.now() + 4000;
  };

  const canOpenNavInline = React.useMemo(() => containerWidth >= 280 + 640 + (isAiCollapsed ? 0 : 320), [containerWidth, isAiCollapsed]);
  const canOpenAiInline = React.useMemo(() => containerWidth >= 320 + 640 + (isNavCollapsed ? 0 : 280), [containerWidth, isNavCollapsed]);

  React.useEffect(() => {
    const nav = navPanelRef.current;
    const ai = aiPanelRef.current;
    if (nav) {
      if (isNavCollapsed && !nav.isCollapsed()) nav.collapse();
      if (!isNavCollapsed && nav.isCollapsed()) nav.expand();
    }
    if (ai) {
      if (isAiCollapsed && !ai.isCollapsed()) ai.collapse();
      if (!isAiCollapsed && ai.isCollapsed()) ai.expand();
    }
  }, [isNavCollapsed, isAiCollapsed]);

  React.useEffect(() => {
    const t = setTimeout(() => setDeferHeavy(true), 250);
    return () => clearTimeout(t);
  }, []);

  React.useEffect(() => {
    const el = desktopContainerRef.current;
    if (!el) return;
    const applyResponsive = (width: number) => {
      setContainerWidth(width);
      if (Date.now() < autoSuppressUntilRef.current) return;
      const { navCollapsed, aiCollapsed } = useLearningStore.getState().uiState;
      const nextNavCollapsed = width < 280 + 640;
      let nextAiCollapsed = width < 280 + 640 + 320;
      if (width >= 280 + 640 + 320) {
        nextAiCollapsed = width < 1280;
      }
      if (nextNavCollapsed !== navCollapsed || nextAiCollapsed !== aiCollapsed) {
        updateUIState({ navCollapsed: nextNavCollapsed, aiCollapsed: nextAiCollapsed });
      }
    };
    const ro = new ResizeObserver((entries) => entries[0] && applyResponsive(entries[0].contentRect.width));
    ro.observe(el);
    const initial = el.getBoundingClientRect().width;
    setContainerWidth(initial);
    applyResponsive(initial);
    return () => ro.disconnect();
  }, [updateUIState]);

  const navMinPercent = React.useMemo(() => containerWidth ? Math.min(40, (280 / containerWidth) * 100) : 22, [containerWidth]);
  const contentMinPercent = React.useMemo(() => containerWidth ? Math.min(90, (640 / containerWidth) * 100) : 40, [containerWidth]);
  const aiMinPercent = React.useMemo(() => containerWidth ? Math.min(40, (320 / containerWidth) * 100) : 22, [containerWidth]);

  const NavigationSidebarLazy = React.useMemo(
    () => dynamic(() => import('@/components/NavigationSidebar').then((m) => m.NavigationSidebar), {
      ssr: false,
      loading: () => <div className="p-3 text-sm text-muted-foreground">加载目录...</div>,
    }),
    [],
  );
  const AIChatSidebarLazy = React.useMemo(
    () => dynamic(() => import('@/components/AIChatSidebar').then((m) => m.AIChatSidebar), {
      ssr: false,
      loading: () => <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>,
    }),
    [],
  );

  return (
    <div className="flex flex-col h-screen">
      <LearnNavBar />
      <main className="flex-1 overflow-hidden relative">
        {isNavCollapsed && canOpenNavInline && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="absolute top-1/2 left-4 z-10 h-9 w-9 -translate-y-1/2 hidden md:inline-flex"
                  onClick={toggleNavSidebar}
                >
                  <PanelRightClose className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>展开目录</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {isAiCollapsed && canOpenAiInline && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="absolute top-1/2 right-4 z-10 h-9 w-9 -translate-y-1/2 hidden md:inline-flex"
                  onClick={toggleAiSidebar}
                >
                  <PanelLeftClose className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>展开AI助手</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        <div ref={desktopContainerRef} className="hidden md:flex h-full w-full p-4 bg-background min-w-0 overflow-hidden">
          <ResizablePanelGroup
            direction="horizontal"
            className="w-full min-w-0 overflow-hidden"
            autoSaveId="learn-layout-panels"
          >
            <ResizablePanel
              ref={navPanelRef}
              collapsible
              defaultSize={10}
              minSize={navMinPercent}
              onCollapse={() => updateUIState({ navCollapsed: true })}
              onExpand={() => updateUIState({ navCollapsed: false })}
              className="min-w-0"
            >
              <div className="h-full overflow-hidden min-w-0">
                {deferHeavy ? <NavigationSidebarLazy toggleSidebar={toggleNavSidebar} /> : <div className="p-3 text-sm text-muted-foreground">加载目录...</div>}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle className="opacity-0" />
            <ResizablePanel defaultSize={55} minSize={contentMinPercent} className="min-w-0">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }} className="h-full w-full min-w-0">
                <Card className="h-full w-full p-4 shadow-sm overflow-auto min-w-0">
                  {children ?? null}
                </Card>
              </motion.div>
            </ResizablePanel>
            <ResizableHandle withHandle className="opacity-0" />
            <ResizablePanel
              ref={aiPanelRef}
              collapsible
              defaultSize={20}
              minSize={aiMinPercent}
              onCollapse={() => updateUIState({ aiCollapsed: true })}
              onExpand={() => updateUIState({ aiCollapsed: false })}
              className="min-w-0"
            >
              <div className="h-full pl-4 min-w-0 overflow-hidden">
                {deferHeavy ? <AIChatSidebarLazy toggleSidebar={toggleAiSidebar} /> : <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>}
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
        <div className="md:hidden h-full w-full relative">
          <div className="h-full w-full overflow-auto">{children ?? null}</div>
          <div className="pointer-events-none fixed inset-x-0 bottom-4 flex items-end justify-between px-4 gap-2">
            <Sheet>
              <SheetTrigger asChild><Button size="icon" className="h-12 w-12 rounded-full shadow-md pointer-events-auto" aria-label="打开目录"><List className="h-5 w-5" /></Button></SheetTrigger>
              <SheetContent side="left" className="p-0"><SheetHeader className="p-3 pb-0"><SheetTitle>课程目录</SheetTitle></SheetHeader><div className="h-full overflow-hidden min-w-0">{deferHeavy ? <NavigationSidebarLazy toggleSidebar={() => {}} /> : <div className="p-3 text-sm text-muted-foreground">加载目录...</div>}</div></SheetContent>
            </Sheet>
            <Sheet>
              <SheetTrigger asChild><Button size="icon" className="h-12 w-12 rounded-full shadow-md pointer-events-auto" aria-label="打开AI助手"><Bot className="h-5 w-5" /></Button></SheetTrigger>
              <SheetContent side="right" className="p-0"><SheetHeader className="p-3 pb-0"><SheetTitle>AI 助手</SheetTitle></SheetHeader><div className="h-full overflow-hidden min-w-0 p-3">{deferHeavy ? <AIChatSidebarLazy toggleSidebar={() => {}} /> : <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>}</div></SheetContent>
            </Sheet>
          </div>
        </div>
        <div className="hidden md:block">
          <div className="pointer-events-none fixed inset-x-0 bottom-4 flex items-end justify-between px-4 gap-2">
            {isNavCollapsed && !canOpenNavInline ? <Sheet><SheetTrigger asChild><Button size="icon" className="h-12 w-12 rounded-full shadow-md pointer-events-auto" aria-label="打开目录"><List className="h-5 w-5" /></Button></SheetTrigger><SheetContent side="left" className="p-0"><SheetHeader className="p-3 pb-0"><SheetTitle>课程目录</SheetTitle></SheetHeader><div className="h-full overflow-hidden min-w-0">{deferHeavy ? <NavigationSidebarLazy toggleSidebar={() => {}} /> : <div className="p-3 text-sm text-muted-foreground">加载目录...</div>}</div></SheetContent></Sheet> : <div />}
            {isAiCollapsed && !canOpenAiInline ? <Sheet><SheetTrigger asChild><Button size="icon" className="h-12 w-12 rounded-full shadow-md pointer-events-auto" aria-label="打开AI助手"><Bot className="h-5 w-5" /></Button></SheetTrigger><SheetContent side="right" className="p-0"><SheetHeader className="p-3 pb-0"><SheetTitle>AI 助手</SheetTitle></SheetHeader><div className="h-full overflow-hidden min-w-0 p-3">{deferHeavy ? <AIChatSidebarLazy toggleSidebar={() => {}} /> : <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>}</div></SheetContent></Sheet> : <div />}
          </div>
        </div>
      </main>
    </div>
  );
}

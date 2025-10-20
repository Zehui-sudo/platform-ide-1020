"use client";

import * as React from 'react';
import { motion } from 'framer-motion';
import { LearnNavBar } from '@/components/LearnNavBar';
import dynamic from 'next/dynamic';
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
} from "@/components/ui/tooltip";
import { PanelRightClose, PanelLeftClose, Bot, List } from 'lucide-react';
import type { ImperativePanelHandle } from 'react-resizable-panels';
import { useLearningStore } from '@/store/learningStore';

// 最小宽度（像素）约束
const NAV_MIN_PX = 280;
const CONTENT_MIN_PX = 640;
const AI_MIN_PX = 320;
// 中等屏默认折叠 AI 的阈值（可按需微调）
const MID_SIZE_AI_COLLAPSE_WIDTH = 1280;

// Lazy-load heavy sidebars to reduce first paint work during transition
const NavigationSidebarLazy = dynamic(
  () => import('@/components/NavigationSidebar').then((m) => m.NavigationSidebar),
  {
    ssr: false,
    loading: () => (
      <div className="h-full overflow-hidden min-w-0 p-3 text-sm text-muted-foreground">加载目录...</div>
    ),
  }
);

const AIChatSidebarLazy = dynamic(
  () => import('@/components/AIChatSidebar').then((m) => m.AIChatSidebar),
  {
    ssr: false,
    loading: () => (
      <div className="h-full pl-4 min-w-0 overflow-hidden p-3 text-sm text-muted-foreground">加载 AI 助手...</div>
    ),
  }
);

export default function LearnLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const navPanelRef = React.useRef<ImperativePanelHandle>(null);
  const aiPanelRef = React.useRef<ImperativePanelHandle>(null);
  const desktopContainerRef = React.useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = React.useState<number>(0);
  const { uiState, updateUIState } = useLearningStore();
  const isNavCollapsed = uiState.navCollapsed || false;
  const isAiCollapsed = uiState.aiCollapsed || false;
  const [deferHeavy, setDeferHeavy] = React.useState(false);
  // 用户手动操作后的短暂抑制自动折叠（避免与用户行为打架）
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
    // 抑制自动规则几秒钟
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
    // 抑制自动规则几秒钟
    autoSuppressUntilRef.current = Date.now() + 4000;
  };

  // 容器尺寸变化时动态计算“是否可内联展开”
  const canOpenNavInline = React.useMemo(() => {
    return containerWidth >= NAV_MIN_PX + CONTENT_MIN_PX + (isAiCollapsed ? 0 : AI_MIN_PX);
  }, [containerWidth, isAiCollapsed]);
  const canOpenAiInline = React.useMemo(() => {
    return containerWidth >= AI_MIN_PX + CONTENT_MIN_PX + (isNavCollapsed ? 0 : NAV_MIN_PX);
  }, [containerWidth, isNavCollapsed]);

  // On mount, sync collapsed state from store to panels
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

  // Defer mounting heavy sidebars a tick after route transition
  React.useEffect(() => {
    const t = setTimeout(() => setDeferHeavy(true), 250);
    return () => clearTimeout(t);
  }, []);

  // 桌面布局：根据容器宽度自适应折叠/展开
  React.useEffect(() => {
    const el = desktopContainerRef.current;
    if (!el) return;

    const applyResponsive = (width: number) => {
      setContainerWidth(width);
      // 避免与用户刚刚手动切换打架
      if (Date.now() < autoSuppressUntilRef.current) return;

      // 当前折叠状态
      const { navCollapsed, aiCollapsed } = useLearningStore.getState().uiState;

      let nextNavCollapsed = false;
      let nextAiCollapsed = false;

      if (width >= NAV_MIN_PX + CONTENT_MIN_PX + AI_MIN_PX) {
        // 全部可同时显示；中等屏默认折叠 AI
        nextNavCollapsed = false;
        nextAiCollapsed = width < MID_SIZE_AI_COLLAPSE_WIDTH;
      } else if (width >= NAV_MIN_PX + CONTENT_MIN_PX) {
        // 优先保留内容+目录，折叠 AI
        nextNavCollapsed = false;
        nextAiCollapsed = true;
      } else if (width >= CONTENT_MIN_PX) {
        // 仅保留内容
        nextNavCollapsed = true;
        nextAiCollapsed = true;
      } else {
        // 更窄：在 <md 会走移动端抽屉，这里也折叠两侧
        nextNavCollapsed = true;
        nextAiCollapsed = true;
      }

      if (nextNavCollapsed !== navCollapsed || nextAiCollapsed !== aiCollapsed) {
        updateUIState({ navCollapsed: nextNavCollapsed, aiCollapsed: nextAiCollapsed });
      }
    };

    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) applyResponsive(entry.contentRect.width);
    });
    ro.observe(el);

    // 初始化调用
    const initial = el.getBoundingClientRect().width;
    setContainerWidth(initial);
    applyResponsive(initial);

    return () => ro.disconnect();
  }, [updateUIState]);

  // 将像素级最小宽度转换为当前容器下的百分比，供 Panel minSize 使用
  const navMinPercent = React.useMemo(() => {
    if (!containerWidth) return 22;
    return Math.min(40, (NAV_MIN_PX / containerWidth) * 100);
  }, [containerWidth]);
  const contentMinPercent = React.useMemo(() => {
    if (!containerWidth) return 40;
    return Math.min(90, (CONTENT_MIN_PX / containerWidth) * 100);
  }, [containerWidth]);
  const aiMinPercent = React.useMemo(() => {
    if (!containerWidth) return 22;
    return Math.min(40, (AI_MIN_PX / containerWidth) * 100);
  }, [containerWidth]);

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
        {/* Desktop layout (≥ md): 3-panel resizable */}
        <div ref={desktopContainerRef} className="hidden md:flex h-full w-full p-4 bg-background min-w-0 overflow-hidden">
          <ResizablePanelGroup
            direction="horizontal"
            className="w-full min-w-0 overflow-hidden"
            autoSaveId="learn-layout-panels"
          >
            <ResizablePanel
              ref={navPanelRef}
              collapsible
              defaultSize={20}
              minSize={navMinPercent}
              onCollapse={() => updateUIState({ navCollapsed: true })}
              onExpand={() => updateUIState({ navCollapsed: false })}
              className="min-w-0"
            >
              <div className="h-full overflow-hidden min-w-0">
                {deferHeavy ? (
                  <NavigationSidebarLazy toggleSidebar={toggleNavSidebar} />
                ) : (
                  <div className="p-3 text-sm text-muted-foreground">加载目录...</div>
                )}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle className="opacity-0" />
            <ResizablePanel defaultSize={55} minSize={contentMinPercent} className="min-w-0">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }} className="h-full w-full min-w-0">
                <Card className="h-full w-full p-4 shadow-sm overflow-auto min-w-0">
                  {children}
                </Card>
              </motion.div>
            </ResizablePanel>
            <ResizableHandle withHandle className="opacity-0" />
            <ResizablePanel
              ref={aiPanelRef}
              collapsible
              defaultSize={25}
              minSize={aiMinPercent}
              onCollapse={() => updateUIState({ aiCollapsed: true })}
              onExpand={() => updateUIState({ aiCollapsed: false })}
              className="min-w-0"
            >
              <div className="h-full pl-4 min-w-0 overflow-hidden">
                {deferHeavy ? (
                  <AIChatSidebarLazy toggleSidebar={toggleAiSidebar} />
                ) : (
                  <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>
                )}
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
        {/* Mobile layout (< md): content + floating drawers for Nav & AI */}
        <div className="md:hidden h-full w-full relative">
          <div className="h-full w-full overflow-auto">
            {children}
          </div>
          {/* Floating Triggers */}
          <div className="pointer-events-none fixed inset-x-0 bottom-4 flex items-end justify-between px-4 gap-2">
            {/* Nav Drawer */}
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  size="icon"
                  className="h-12 w-12 rounded-full shadow-md pointer-events-auto"
                  aria-label="打开目录"
                >
                  <List className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0">
                <SheetHeader className="p-3 pb-0">
                  <SheetTitle>课程目录</SheetTitle>
                </SheetHeader>
                <div className="h-full overflow-hidden min-w-0">
                  {deferHeavy ? (
                    <NavigationSidebarLazy toggleSidebar={() => {}} />
                  ) : (
                    <div className="p-3 text-sm text-muted-foreground">加载目录...</div>
                  )}
                </div>
              </SheetContent>
            </Sheet>

            {/* AI Drawer */}
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  size="icon"
                  className="h-12 w-12 rounded-full shadow-md pointer-events-auto"
                  aria-label="打开AI助手"
                >
                  <Bot className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="p-0">
                <SheetHeader className="p-3 pb-0">
                  <SheetTitle>AI 助手</SheetTitle>
                </SheetHeader>
                <div className="h-full overflow-hidden min-w-0 p-3">
                  {deferHeavy ? (
                    <AIChatSidebarLazy toggleSidebar={() => {}} />
                  ) : (
                    <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>

        {/* Desktop floating drawers (≥ md & 窄宽度): 左右橙色圆按钮触发 Sheet */}
        <div className="hidden md:block">
          <div className="pointer-events-none fixed inset-x-0 bottom-4 flex items-end justify-between px-4 gap-2">
            {/* 当目录折叠且不可内联展开时，显示左侧浮动按钮 */}
            {isNavCollapsed && !canOpenNavInline ? (
              <Sheet>
                <SheetTrigger asChild>
                  <Button
                    size="icon"
                    className="h-12 w-12 rounded-full shadow-md pointer-events-auto"
                    aria-label="打开目录"
                  >
                    <List className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0">
                  <SheetHeader className="p-3 pb-0">
                    <SheetTitle>课程目录</SheetTitle>
                  </SheetHeader>
                  <div className="h-full overflow-hidden min-w-0">
                    {deferHeavy ? (
                      <NavigationSidebarLazy toggleSidebar={() => {}} />
                    ) : (
                      <div className="p-3 text-sm text-muted-foreground">加载目录...</div>
                    )}
                  </div>
                </SheetContent>
              </Sheet>
            ) : (
              <div />
            )}

            {/* 当 AI 折叠且不可内联展开时，显示右侧浮动按钮 */}
            {isAiCollapsed && !canOpenAiInline ? (
              <Sheet>
                <SheetTrigger asChild>
                  <Button
                    size="icon"
                    className="h-12 w-12 rounded-full shadow-md pointer-events-auto"
                    aria-label="打开AI助手"
                  >
                    <Bot className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="p-0">
                  <SheetHeader className="p-3 pb-0">
                    <SheetTitle>AI 助手</SheetTitle>
                  </SheetHeader>
                  <div className="h-full overflow-hidden min-w-0 p-3">
                    {deferHeavy ? (
                      <AIChatSidebarLazy toggleSidebar={() => {}} />
                    ) : (
                      <div className="p-3 text-sm text-muted-foreground">加载 AI 助手...</div>
                    )}
                  </div>
                </SheetContent>
              </Sheet>
            ) : (
              <div />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

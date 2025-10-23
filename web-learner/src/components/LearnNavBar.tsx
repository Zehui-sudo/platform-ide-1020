
"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useMemo } from "react";
import { useLearningStore } from "@/store/learningStore";
import { useHydratedStore } from "@/hooks/useHydratedStore";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Home, ChevronLeft, ChevronRight, Type, ALargeSmall } from "lucide-react";
import { ThemeGenerator } from "@/components/ThemeGenerator";
import { useEffect, useState } from "react";

type LearnFontItem = {
  id: string;
  fontFamily: string;
  displayName: string;
};

export function LearnNavBar() {
  const hydrated = useHydratedStore();
  const router = useRouter();
  const { currentPath, currentSection, loadPath, loadSection, fontSize, setFontSize, userProgress } = useLearningStore();
  const fontFamilyId = useLearningStore((s) => s.fontFamilyId);
  const setFontFamily = useLearningStore((s) => s.setFontFamily);
  const availableSubjects = useLearningStore((state) => state.availableSubjects);
  const subjectLabels = useLearningStore((state) => state.subjectLabels);
  // Icons are no longer used in the subject selector

  const subjectItems = useMemo(() => {
    const codes = (availableSubjects && availableSubjects.length > 0)
      ? availableSubjects
      : (['python','javascript','langgraph','astrology'] as string[]);
    const toFallbackLabel = (v: string) => (
      v === 'astrology' ? '占星学' : (v === 'langgraph' ? 'LangGraph' : (v.charAt(0).toUpperCase() + v.slice(1)))
    );
    const items = codes.map(v => ({
      value: v as string,
      label: (hydrated && subjectLabels && subjectLabels[v]) ? subjectLabels[v] : toFallbackLabel(v)
    }));

    // Sort: English-first labels A-Z, then Chinese/non-English by locale
    const isEnglish = (s: string) => /^[A-Za-z]/.test(s.trim());
    const collatorEn = new Intl.Collator('en', { sensitivity: 'base' });
    const collatorZh = new Intl.Collator('zh-Hans', { sensitivity: 'base' });
    const enItems = items.filter(it => isEnglish(it.label)).sort((a, b) => collatorEn.compare(a.label, b.label));
    const zhItems = items.filter(it => !isEnglish(it.label)).sort((a, b) => collatorZh.compare(a.label, b.label));
    return [...enItems, ...zhItems];
  }, [availableSubjects, subjectLabels, hydrated]);

  const selectedSubject = subjectItems.find(l => l.value === (currentPath?.subject || ''));

  // Dynamic fonts loaded from generated manifest
  const [fontItems, setFontItems] = useState<LearnFontItem[]>([]);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch('/learn-fonts.json', { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json() as LearnFontItem[];
        if (mounted) setFontItems(data);
      } catch {}
    })();
    return () => { mounted = false; };
  }, []);

  const {
    allSections,
    currentSectionIndex,
    currentChapterTitle,
    progressValue,
    language: subject,
    completedCount,
  } = useMemo(() => {
    if (!currentPath || !currentSection) {
      return {
        allSections: [],
        currentSectionIndex: -1,
        currentChapterTitle: "",
        progressValue: 0,
        subject: '',
        sectionId: '',
        completedCount: 0
      };
    }

    const sections = currentPath.chapters.flatMap((ch) =>
      (ch.sections && ch.sections.length > 0)
        ? ch.sections
        : (ch.groups || []).flatMap(g => g.sections)
    );
    const currentIndex = sections.findIndex((s) => s.id === currentSection.id);
    const chapter = currentPath.chapters.find((ch) => {
      const secs = (ch.sections && ch.sections.length > 0) ? ch.sections : (ch.groups || []).flatMap(g => g.sections);
      return secs.some(section => section.id === currentSection.id);
    });
    
    // 只计算当前语言路径下的章节完成情况
    const currentPathSectionIds = sections.map(s => s.id);
    const completed = Object.entries(userProgress)
      .filter(([sectionId, progress]) => 
        currentPathSectionIds.includes(sectionId) && progress.isCompleted
      ).length;
    
    const progress = sections.length > 0 ? (completed / sections.length) * 100 : 0;

    return {
      allSections: sections,
      currentSectionIndex: currentIndex,
      currentChapterTitle: chapter?.title || "",
      progressValue: progress,
      language: currentPath.subject,
      sectionId: currentSection.id,
      completedCount: completed
    };
  }, [currentPath, currentSection, userProgress]);

  const handleSubjectChange = (newSubject: string) => {
    if (newSubject !== subject) {
      loadPath(newSubject);
      router.replace(`/learn?subject=${newSubject}`);
    }
  };

  const navigateToSection = (offset: number) => {
    const newIndex = currentSectionIndex + offset;
    if (newIndex >= 0 && newIndex < allSections.length) {
      const newSection = allSections[newIndex];
      loadSection(newSection.id);
    }
  };

  if (!currentPath) {
    // You might want a more sophisticated loading skeleton here
    return (
      <div className="flex items-center justify-between px-4 py-2 border-b bg-background h-16">
        <div className="animate-pulse bg-gray-200 h-8 w-32 rounded"></div>
        <div className="animate-pulse bg-gray-200 h-8 w-48 rounded"></div>
        <div className="animate-pulse bg-gray-200 h-8 w-24 rounded"></div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <header className="flex items-center justify-between h-16 px-4 md:px-6 border-b">
        {/* Left Section */}
        <div className="flex items-center gap-2 md:gap-4">
          <Link href="/" className="hidden md:flex items-center gap-2 font-semibold">
            <Image
              src="/principal-logo.png"
              alt="Principal"
              width={140}
              height={40}
              className="h-8 w-auto"
              priority
            />
          </Link>
          <Select
            value={subject as string}
            onValueChange={(value) => handleSubjectChange(value)}
          >
            <SelectTrigger className="w-[180px] md:w-[200px]">
              <div className="flex items-center gap-2 min-w-0">
                {selectedSubject ? (
                  <span className="truncate font-bold">{selectedSubject.label}</span>
                ) : (
                  <SelectValue placeholder="选择语言" />
                )}
              </div>
            </SelectTrigger>
            <SelectContent className="w-[180px] md:w-[200px]">
              {subjectItems.map((lang) => (
                <SelectItem
                  key={lang.value}
                  value={lang.value}
                  className="whitespace-normal min-h-auto pr-8"
                >
                  <span className="leading-tight">{lang.label}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <ThemeGenerator />
        </div>

        {/* Center Section */}
        <div className="flex-1 flex items-center justify-center gap-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigateToSection(-1)}
                disabled={currentSectionIndex <= 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>上一节</p>
            </TooltipContent>
          </Tooltip>
          <div className="text-center">
            <p className="text-sm font-medium truncate">{currentChapterTitle}</p>
            <p className="text-xs text-muted-foreground truncate">
              {allSections[currentSectionIndex]?.title}
            </p>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigateToSection(1)}
                disabled={currentSectionIndex >= allSections.length - 1}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>下一节</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Right Section (hidden on < md to keep navbar compact) */}
        <div className="hidden md:flex items-center gap-4">
          {/* 进度条：仅在更宽的屏幕显示，优先隐藏 */}
          <div className="hidden lg:flex items-center gap-2 w-40">
            <Progress value={progressValue} className="w-full" />
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              已完成 {completedCount}/{allSections.length}
            </span>
          </div>
          {/* Font family selector */}
          <DropdownMenu>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Type className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              <TooltipContent>
                <p>调节字体风格</p>
              </TooltipContent>
            </Tooltip>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>字体风格</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup
                value={fontFamilyId || "system"}
                onValueChange={(value) => {
                  if (value === 'system') {
                    setFontFamily(null, null);
                  } else {
                    const picked = fontItems.find(f => f.id === value);
                    if (picked) setFontFamily(picked.id, picked.fontFamily);
                  }
                }}
              >
                <DropdownMenuRadioItem value="system">
                  <span style={{ fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", PingFang SC, "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "Helvetica Neue", Arial, sans-serif' }}>系统默认</span>
                </DropdownMenuRadioItem>
                {fontItems.map((f) => (
                  <DropdownMenuRadioItem key={f.id} value={f.id}>
                    <span style={{ fontFamily: f.fontFamily }}>{f.displayName}</span>
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Font size selector */}
          <DropdownMenu>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <ALargeSmall className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              <TooltipContent>
                <p>调节字体大小</p>
              </TooltipContent>
            </Tooltip>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuLabel>字体大小</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup value={fontSize.toString()} onValueChange={(value) => setFontSize(parseInt(value))}>
                <DropdownMenuRadioItem value="14">14px 小</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="16">16px 默认</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="18">18px 大</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="20">20px 特大</DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" asChild>
                <Link href="/">
                  <Home className="h-4 w-4" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>返回主页</p>
            </TooltipContent>
          </Tooltip>
        </div>
        {/* 小屏时不显示进度条，以保留其他控件可见性 */}
      </header>
    </TooltipProvider>
  );
}

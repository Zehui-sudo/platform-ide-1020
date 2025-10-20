"use client";

import { useId, useMemo, useState } from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
  const reactId = useId();
  const { gradientId, gradientClass } = useMemo(() => {
    const safe = reactId.replace(/[^a-zA-Z0-9_-]/g, "");
    return {
      gradientId: `sparkles-gemini-${safe}`,
      gradientClass: `sparkles-grad-${safe}`,
    };
  }, [reactId]);

  const handleGenerate = async () => {
    if (!themeName.trim() || !content.trim()) {
      return;
    }

    setIsGenerating(true);
    try {
      // TODO: 实现生成主题的逻辑
      console.log("生成主题:", { themeName, content, generationStyle });

      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 2000));

      // 生成成功后关闭表单
      setIsOpen(false);
      setThemeName("");
      setContent("");
    } catch (error) {
      console.error("生成主题失败:", error);
    } finally {
      setIsGenerating(false);
    }
  };

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

        <PopoverContent className="w-80 p-4" align="center" side="bottom">
          <div className="space-y-3">
            <h4 className="font-medium text-sm leading-none">生成学习主题</h4>
            <p className="text-xs text-muted-foreground">
              输入主题名称和内容，生成个性化学习路径
            </p>

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
                  className={cn(
                    "h-8 text-xs",
                    generationStyle === 'principle' && "bg-primary/80 hover:bg-primary/70"
                  )}
                >
                  原理学习
                </Button>
                <Button
                  variant={generationStyle === 'preview' ? 'default' : 'outline'}
                  onClick={() => setGenerationStyle('preview')}
                  className={cn(
                    "h-8 text-xs",
                    generationStyle === 'preview' && "bg-primary/80 hover:bg-primary/70"
                  )}
                >
                  深度预习
                </Button>
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
              >
                {isGenerating ? "生成中..." : "生成"}
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </TooltipProvider>
  );
}

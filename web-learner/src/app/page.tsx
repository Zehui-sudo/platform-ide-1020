// src/app/page.tsx
"use client";

import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { HeroHighlight } from "@/components/ui/hero-highlight";
import { HandWrittenTitle } from "@/components/ui/hand-writing-text";
import { useRouter } from "next/navigation";
import localFont from "next/font/local";
import Link from "next/link";

const smileySans = localFont({
  src: [
    { path: "../../public/fonts/smiley-sans/SmileySans-Oblique.otf.woff2", weight: "400", style: "normal" },
    { path: "../../public/fonts/smiley-sans/SmileySans-Oblique.ttf.woff2", weight: "400", style: "normal" },
  ],
  display: "swap",
  fallback: [
    "system-ui",
    "-apple-system",
    "Segoe UI",
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "Noto Sans CJK SC",
    "Helvetica Neue",
    "Arial",
    "sans-serif",
  ],
});

export default function HomePage() {
  const router = useRouter();

  // Prefetch learn route to reduce blocking on transition
  useEffect(() => {
    try {
      if (router.prefetch) {
        router.prefetch("/learn?subject=python");
      }
    } catch {}
  }, [router]);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    const { clientX, clientY } = e;
    try {
      window.dispatchEvent(
        new CustomEvent("start-route-transition", { detail: { x: clientX, y: clientY } })
      );
    } catch {}
    // Start navigation immediately for overlapping transition
    setTimeout(() => {
      router.push("/learn?subject=python");
    }, 300);
  };

  return (
    <div className={smileySans.className}>
      {/* Hidden link as a secondary prefetch hint */}
      <Link href="/learn?subject=python" prefetch aria-hidden className="sr-only">
        Prefetch Learn
      </Link>

      <motion.div initial={{ opacity: 1 }} animate={{ opacity: 1 }}>
        <HeroHighlight
          containerClassName="relative w-full h-screen bg-white text-foreground overflow-hidden"
          className="w-full h-full"
        >
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-start pointer-events-none space-y-2 md:space-y-8">
              <h1 className="text-3xl sm:text-5xl md:text-7xl font-bold tracking-[0.44em]">
                探究·拆解·
                <span className="relative z-0 inline-block after:absolute after:content-[''] after:left-0 after:right-0 after:bottom-[-0.05em] after:h-[0.4em] after:bg-gradient-to-r after:from-[#ffa04f] after:to-amber-300 after:rounded-sm after:-z-10 after:translate-x-[-0.2em]">
                  原理
                </span>
              </h1>
              <p className="text-xs md:text-2xl text-muted-foreground tracking-[0.3em]">
                以直击核心的方式，从原理开始学习
              </p>
            </div>
            <HandWrittenTitle
              onClick={handleClick}
              titleClassName="text-3xl md:text-3xl bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text bg-no-repeat bg-[length:0%_100%] transition-all duration-300 ease-in-out hover:text-transparent hover:bg-[length:100%_100%]"
              subtitleClassName="bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text bg-no-repeat bg-[length:0%_100%] transition-all duration-300 ease-in-out hover:text-transparent hover:bg-[length:100%_100%]"
              title="现在！开始学习！"
              subtitle="Start Learning Now"
              scale={0.7}
              className="mx-auto relative z-30 mt-32"
            />
          </div>
        </HeroHighlight>
      </motion.div>

      {/* overlay handled globally in PageLayout for cross-route animation */}
    </div>
  );
}

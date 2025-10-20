"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useLearningStore } from "@/store/learningStore";
import { AnimatePresence, motion } from "framer-motion";

function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <h1 className="text-xl font-bold">Dashboard</h1>
        <Avatar>
          <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
          <AvatarFallback>CN</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}

export function PageLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLearnPage = pathname.startsWith('/learn');
  const isHomePage = pathname === '/';
  const initializeAllPaths = useLearningStore(state => state.initializeAllPaths);
  const [overlay, setOverlay] = useState<{ active: boolean; x: number; y: number; radius: number; color?: string }>(() => ({ active: false, x: 0, y: 0, radius: 0 }));
  
  useEffect(() => {
    // 在应用启动时初始化所有语言的学习路径
    initializeAllPaths();
  }, [initializeAllPaths]);

  // Listen for route transition overlay trigger
  useEffect(() => {
    type RouteTransitionEvent = CustomEvent<{ x: number; y: number; color?: string }>;
    const handler = (e: RouteTransitionEvent) => {
      try {
        const detail = e.detail;
        if (!detail) return;
        const { x, y, color } = detail;
        // Calculate max radius to cover the viewport from the click point
        const sw = window.innerWidth;
        const sh = window.innerHeight;
        const xDist = Math.max(x, sw - x);
        const yDist = Math.max(y, sh - y);
        const radius = Math.sqrt(xDist ** 2 + yDist ** 2);

        setOverlay({ active: true, x, y, radius, color });
        // Auto hide after animation duration (match ~500ms)
        setTimeout(() => setOverlay(prev => ({ ...prev, active: false })), 550);
      } catch {}
    };
    window.addEventListener("start-route-transition", handler as EventListener);
    return () => window.removeEventListener("start-route-transition", handler as EventListener);
  }, []);

  if (isLearnPage || isHomePage) {
    return (
      <>
        {children}
        {/* Global route transition overlay */}
        <AnimatePresence>
          {overlay.active && (
            <motion.div
              key="route-overlay"
              className="fixed top-0 left-0 bg-background z-50"
              style={{
                width: overlay.radius * 2,
                height: overlay.radius * 2,
                top: overlay.y - overlay.radius,
                left: overlay.x - overlay.radius,
                borderRadius: "50%",
                // If a color is provided by the sender, use it to match the page background color
                backgroundColor: overlay.color ?? undefined,
              }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          )}
        </AnimatePresence>
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="container mx-auto p-4">{children}</main>
    </>
  );
}

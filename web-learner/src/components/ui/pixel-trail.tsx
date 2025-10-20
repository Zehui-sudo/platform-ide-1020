"use client";

import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { motion, useAnimationControls } from "framer-motion";
import { cn } from "@/lib/utils";
import { useDimensions } from "@/hooks/use-debounced-dimensions";

interface PixelTrailProps {
  pixelSize?: number;
  fadeDuration?: number; // ms
  delay?: number; // ms
  radius?: number; // how many neighbor rings to animate
  className?: string;
  pixelClassName?: string;
}

// PixelTrail listens to global mousemove to avoid blocking clicks.
// It renders an absolute grid and fades dots where the cursor passes.
export function PixelTrail({
  pixelSize = 20,
  fadeDuration = 500,
  delay = 0,
  radius = 2,
  className,
  pixelClassName,
}: PixelTrailProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const idPrefixRef = useRef<string>(
    typeof crypto !== "undefined" && (crypto as any).randomUUID
      ? (crypto as any).randomUUID()
      : Math.random().toString(36).slice(2)
  );

  const dimensions = useDimensions(containerRef);

  const columns = useMemo(
    () => (pixelSize > 0 ? Math.ceil(dimensions.width / pixelSize) : 0),
    [dimensions.width, pixelSize]
  );
  const rows = useMemo(
    () => (pixelSize > 0 ? Math.ceil(dimensions.height / pixelSize) : 0),
    [dimensions.height, pixelSize]
  );

  const animateAt = useCallback(
    (clientX: number, clientY: number) => {
      if (!containerRef.current || pixelSize <= 0) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = Math.floor((clientX - rect.left) / pixelSize);
      const y = Math.floor((clientY - rect.top) / pixelSize);
      if (x < 0 || y < 0 || x >= columns || y >= rows) return;
      // Animate the center cell and its neighbors within `radius`
      for (let dy = -radius; dy <= radius; dy++) {
        for (let dx = -radius; dx <= radius; dx++) {
          const nx = x + dx;
          const ny = y + dy;
          if (nx < 0 || ny < 0 || nx >= columns || ny >= rows) continue;
          const el = document.getElementById(`${idPrefixRef.current}-pixel-${nx}-${ny}`);
          if (!el) continue;
          const animatePixel = (el as any).__animatePixel as undefined | (() => void);
          if (animatePixel) animatePixel();
        }
      }
    },
    [columns, rows, pixelSize, radius]
  );

  useEffect(() => {
    const handler = (e: MouseEvent) => animateAt(e.clientX, e.clientY);
    window.addEventListener("mousemove", handler, { passive: true });
    return () => window.removeEventListener("mousemove", handler as any);
  }, [animateAt]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "absolute inset-0 w-full h-full pointer-events-none z-10",
        className
      )}
      aria-hidden
    >
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <PixelDot
              key={`${colIndex}-${rowIndex}`}
              id={`${idPrefixRef.current}-pixel-${colIndex}-${rowIndex}`}
              size={pixelSize}
              fadeDuration={fadeDuration}
              delay={delay}
              className={pixelClassName}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

interface PixelDotProps {
  id: string;
  size: number;
  fadeDuration: number;
  delay: number;
  className?: string;
}

const PixelDot: React.FC<PixelDotProps> = React.memo(
  ({ id, size, fadeDuration, delay, className }) => {
    const controls = useAnimationControls();

    const animatePixel = useCallback(() => {
      controls.start({
        opacity: [1, 0],
        transition: { duration: fadeDuration / 1000, delay: delay / 1000 },
      });
    }, [controls, fadeDuration, delay]);

    const ref = useCallback((node: HTMLDivElement | null) => {
      if (node) (node as any).__animatePixel = animatePixel;
    }, [animatePixel]);

    return (
      <motion.div
        id={id}
        ref={ref}
        className={cn("pointer-events-none", className)}
        style={{ width: `${size}px`, height: `${size}px` }}
        initial={{ opacity: 0 }}
        animate={controls}
        exit={{ opacity: 0 }}
      />
    );
  }
);

PixelDot.displayName = "PixelDot";

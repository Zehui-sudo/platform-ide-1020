"use client";
import { cn } from "@/lib/utils";
import { useMotionValue, motion, useMotionTemplate } from "framer-motion";
import React from "react";

export const HeroHighlight = ({
  children,
  className,
  containerClassName,
  showHighlight = true,
}: {
  children?: React.ReactNode;
  className?: string;
  containerClassName?: string;
  showHighlight?: boolean;
}) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const resolvedChildren = (children ?? null) as any;
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({
    currentTarget,
    clientX,
    clientY,
  }: React.MouseEvent<HTMLDivElement>) {
    if (!currentTarget) return;
    const { left, top } = currentTarget.getBoundingClientRect();

    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  const dotPattern = (color: string) => ({
    backgroundImage: `radial-gradient(circle, ${color} 1.25px, transparent 1.25px)`,
    backgroundSize: "14px 14px",
  });

  return (
    <div
      className={cn(
        "relative isolate h-[40rem] flex items-center bg-background justify-center w-full group",
        containerClassName,
      )}
      onMouseMove={handleMouseMove}
    >
      <div
        className="absolute inset-0 pointer-events-none opacity-100 z-0"
        style={dotPattern("rgba(0,0,0,0.08)")}
      />
      <div
        className="absolute inset-0 opacity-0 dark:opacity-60 pointer-events-none z-0"
        style={dotPattern("rgba(255,255,255,0.12)")}
      />
      {showHighlight && (
        <motion.div
          className="pointer-events-none absolute inset-0 opacity-0 transition duration-300 group-hover:opacity-100 z-10"
          style={{
            ...dotPattern("rgb(255 160 79)"),
            WebkitMaskImage: useMotionTemplate`
              radial-gradient(
                200px circle at ${mouseX}px ${mouseY}px,
                black 0%,
                transparent 100%
              )
            `,
            maskImage: useMotionTemplate`
              radial-gradient(
                200px circle at ${mouseX}px ${mouseY}px,
                black 0%,
                transparent 100%
              )
            `,
          }}
        />
      )}

      <div className={cn("relative z-30", className)}>{resolvedChildren}</div>
    </div>
  );
};

export const Highlight = ({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
}) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const resolvedChildren = (children ?? null) as any;
  return (
    <motion.span
      initial={{
        backgroundSize: "0% 100%",
      }}
      animate={{
        backgroundSize: "100% 100%",
      }}
      transition={{
        duration: 2,
        ease: "linear",
        delay: 0.5,
      }}
      style={{
        backgroundRepeat: "no-repeat",
        backgroundPosition: "left center",
        display: "inline",
      }}
      className={cn(
        "relative inline-block pb-1 px-1 rounded-lg bg-gradient-to-r from-orange-300 to-amber-300 dark:from-orange-500 dark:to-amber-500",
        className,
      )}
    >
      {resolvedChildren}
    </motion.span>
  );
};

"use client"

import type { CSSProperties } from "react"

import { motion } from "framer-motion"

import { cn } from "@/lib/utils"

interface HandWrittenTitleProps {
  title?: string
  subtitle?: string
  className?: string
  scale?: number
  style?: CSSProperties
  titleClassName?: string
  subtitleClassName?: string
  titleStyle?: CSSProperties
  subtitleStyle?: CSSProperties
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void
}

function HandWrittenTitle({
  title = "Hand Written",
  subtitle = "Optional subtitle",
  className,
  scale = 1,
  style,
  titleClassName,
  subtitleClassName,
  titleStyle,
  subtitleStyle,
  onClick,
}: HandWrittenTitleProps) {
  const draw = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: {
      pathLength: 1,
      opacity: 1,
      transition: {
        pathLength: { duration: 2.5, ease: [0.43, 0.13, 0.23, 0.96] },
        opacity: { duration: 0.5 },
      },
    },
  }

  // Real (layout) scaling: adjust maxWidth, vertical padding, and text sizes
  const baseMaxWidthRem = 56 // Tailwind max-w-4xl
  const basePaddingYRem = 6 // Tailwind py-24

  const scaleSafe = Number.isFinite(scale) && scale > 0 ? scale : 1

  const layoutScaleStyle: CSSProperties = {
    maxWidth: `${baseMaxWidthRem * scaleSafe}rem`,
    paddingTop: `${basePaddingYRem * scaleSafe}rem`,
    paddingBottom: `${basePaddingYRem * scaleSafe}rem`,
  }

  // Merge with user-provided style (user style wins)
  const mergedStyle: CSSProperties = {
    ...layoutScaleStyle,
    ...(style ?? {}),
  }

  return (
    <div
      className={cn(
        "relative w-full max-w-4xl mx-auto pointer-events-none",
        className,
      )}
      style={mergedStyle}
    >
      <div className="absolute inset-0 pointer-events-none">
        <motion.svg
          width="100%"
          height="100%"
          viewBox="0 0 1200 600"
          initial="hidden"
          animate="visible"
          className="w-full h-full"
        >
          <title>KokonutUI</title>
          <motion.path
            d="M 950 90 
                           C 1250 300, 1050 480, 600 520
                           C 250 520, 150 480, 150 300
                           C 150 120, 350 80, 600 80
                           C 850 80, 950 180, 950 180"
            fill="none"
            strokeWidth="12"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            variants={draw}
            className="text-black dark:text-white opacity-90"
          />
        </motion.svg>
      </div>
      <div
        className={cn(
          "relative text-center z-10 flex flex-col items-center justify-center pointer-events-auto",
          {
            "cursor-pointer": !!onClick,
          },
        )}
        onClick={onClick}
      >
        <motion.h1
          className={cn(
            "text-4xl md:text-6xl text-black dark:text-white tracking-tighter flex items-center gap-2",
            titleClassName,
          )}
          style={titleStyle}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.8 }}
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            className={cn("text-xl text-black/80 dark:text-white/80", subtitleClassName)}
            style={subtitleStyle}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.8 }}
          >
            {subtitle}
          </motion.p>
        )}
      </div>
    </div>
  )
}

export { HandWrittenTitle }

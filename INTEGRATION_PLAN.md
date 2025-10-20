# `framer-pixel-flow` to `web-learner` Integration Plan

## 1. Objective

To migrate the functionality and styling of the `framer-pixel-flow` Vite application into the `web-learner` Next.js application. The end goal is to make the `framer-pixel-flow` interface the true homepage of `web-learner`, allowing for a single, unified deployment on Vercel.

---

## 2. Analysis Summary

- **`framer-pixel-flow`** is a standard Vite + React project using `shadcn/ui` for components and Tailwind CSS for styling. Its primary purpose is to serve as a visually appealing landing page with a specific "circular reveal" animation on navigation.
- **`web-learner`** is a Next.js 15 application using the App Router. It also uses `shadcn/ui` and Tailwind CSS, but its theme and component set are less comprehensive than `framer-pixel-flow`.
- The core homepage logic in both projects is very similar. The main task is to transfer the superior animation logic, the complete `shadcn/ui` component set, and the full theme from `framer-pixel-flow` to `web-learner`.

---

## 3. Execution Steps

### Step 3.1: Dependency Migration

The `framer-pixel-flow` project contains numerous UI and utility packages that are missing from `web-learner`. These will be added to the `web-learner` workspace.

**Action:** Execute the following command to install missing dependencies into `web-learner`.

```bash
pnpm add --filter @platform-ide/web-learner tailwindcss-animate sonner recharts embla-carousel-react vaul class-variance-authority tailwind-merge
```
*(Note: Many `@radix-ui` components are already present or will be added via shadcn CLI if needed. The most critical missing plugins and libraries are listed above.)*

### Step 3.2: Component & Hook Migration

All UI components and custom hooks from `framer-pixel-flow` will be moved directly into the `web-learner` application.

**Action:**
1. Move the entire `ui` components directory:
   ```bash
   mv ./framer-pixel-flow/src/components/ui ./web-learner/src/components/
   ```
2. Move the custom hooks directory:
   ```bash
   mv ./framer-pixel-flow/src/components/hooks ./web-learner/src/components/
   ```

### Step 3.3: Styling & Theme Integration

The Tailwind CSS configuration will be merged to ensure the complete theme from `framer-pixel-flow` is available in `web-learner`.

**Action:** Overwrite the contents of `web-learner/tailwind.config.mjs` with the following consolidated configuration. This combines the Next.js setup with the rich `shadcn/ui` theme.

```javascript
/** @type {import('tailwindcss').Config} */
const config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        sans: [
          "Smiley Sans",
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
          "Apple Color Emoji",
          "Segoe UI Emoji",
          "Noto Color Emoji",
        ],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

### Step 3.4: Homepage Logic Integration

The homepage of `web-learner` (`src/app/page.tsx`) will be replaced with a new version that incorporates the superior animation and navigation logic from `framer-pixel-flow`.

**Action:** Overwrite the contents of `web-learner/src/app/page.tsx` with the code below.

```tsx
// src/app/page.tsx
"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useScreenSize } from "@/components/hooks/use-screen-size";
import { HandWrittenTitle } from "@/components/ui/hand-writing-text";
import { HeroHighlight } from "@/components/ui/hero-highlight";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function HomePage() {
  const router = useRouter();
  const [isAnimating, setIsAnimating] = useState(false);
  const [clickPosition, setClickPosition] = useState({ x: 0, y: 0 });

  // Prefetch learn route to reduce blocking on transition
  useEffect(() => {
    router.prefetch("/learn?language=python");
  }, [router]);

  const calculateRadius = (x: number, y: number) => {
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    const xDist = Math.max(x, screenWidth - x);
    const yDist = Math.max(y, screenHeight - y);
    return Math.sqrt(xDist ** 2 + yDist ** 2);
  };

  const radius = typeof window !== "undefined" ? calculateRadius(clickPosition.x, clickPosition.y) : 0;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    setClickPosition({ x: e.clientX, y: e.clientY });
    setIsAnimating(true);
  };

  const handleAnimationComplete = () => {
    // Navigate after the animation completes
    router.push("/learn?language=python");
  };

  return (
    <>
      {/* Hidden link as a secondary prefetch hint */}
      <Link href="/learn?language=python" prefetch aria-hidden className="sr-only">
        Prefetch Learn
      </Link>

      <AnimatePresence>
        {!isAnimating && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
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
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isAnimating && (
          <motion.div
            className="fixed top-0 left-0 bg-white z-50"
            style={{
              width: radius * 2,
              height: radius * 2,
              top: clickPosition.y - radius,
              left: clickPosition.x - radius,
              borderRadius: "50%",
            }}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            onAnimationComplete={handleAnimationComplete}
          />
        )}
      </AnimatePresence>
    </>
  );
}
```

### Step 3.5: Cleanup

Once the integration is verified to be working correctly, the original `framer-pixel-flow` directory will no longer be needed.

**Action:** Execute the following command to remove the directory.

```bash
rm -rf ./framer-pixel-flow
```

---

## 4. Validation

After all steps are completed, validate the integration by:
1. Running the development server: `pnpm dev:web`.
2. Opening the browser to `http://localhost:3000`.
3. Verifying that the `framer-pixel-flow` homepage appears and that the click animation correctly transitions to the `/learn` page.

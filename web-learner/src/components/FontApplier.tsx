"use client";

import { useEffect } from "react";
import { useLearningStore } from "@/store/learningStore";

// Applies the selected font family globally to the document body.
// Code blocks use explicit font-mono so they remain unaffected.
export function FontApplier() {
  const fontFamily = useLearningStore((s) => s.fontFamily ?? null);

  useEffect(() => {
    try {
      const fallback = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", PingFang SC, "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "Helvetica Neue", Arial, sans-serif';
      if (typeof document !== 'undefined') {
        if (fontFamily && fontFamily.trim().length > 0) {
          document.body.style.setProperty('font-family', `${fontFamily}, ${fallback}`, 'important');
          document.body.setAttribute('data-app-font', fontFamily);
        } else {
          document.body.style.removeProperty('font-family');
          document.body.removeAttribute('data-app-font');
        }
      }
    } catch {}
  }, [fontFamily]);

  return null;
}

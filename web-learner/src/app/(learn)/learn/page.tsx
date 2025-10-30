"use client";

import * as React from "react";
import { ContentDisplay } from '@/components/ContentDisplay';

// It's a best practice to wrap the component that uses useSearchParams in a client component.
// The page is already a client component, but for Suspense, it's cleaner this way.
function LearnPageContent() {
  // Route synchronization is now handled only in layout.tsx
  // This component focuses solely on content display
  console.log('%c[Page] 渲染', 'color: lightgray', {
    timestamp: new Date().toISOString()
  });

  return <ContentDisplay />;
}

// The page component itself, which sets up the Suspense boundary
export default function LearnPage() {
  return React.createElement(
    React.Suspense,
    { fallback: <div>Loading...</div> },
    React.createElement(LearnPageContent),
  );
}

"use client";

import * as React from "react";
import { useSearchParams } from 'next/navigation';
import { useLearningStore } from '@/store/learningStore';
import { ContentDisplay } from '@/components/ContentDisplay';

// It's a best practice to wrap the component that uses useSearchParams in a client component.
// The page is already a client component, but for Suspense, it's cleaner this way.
function LearnPageContent() {
  const loadPath = useLearningStore((state) => state.loadPath);
  const loadSection = useLearningStore((state) => state.loadSection);
  const currentPath = useLearningStore((state) => state.currentPath);
  const searchParams = useSearchParams();
  const subjectFromUrl = searchParams.get('subject') ?? searchParams.get('language');
  const sectionFromUrl = searchParams.get('section');

  React.useEffect(() => {
    const currentSubject = currentPath?.subject;

    // URL is the source of truth. Sync it with the store.
    if (subjectFromUrl && subjectFromUrl !== currentSubject) {
      loadPath(subjectFromUrl);
    } else if (!subjectFromUrl && !currentSubject) {
      // Fallback for initial load if URL has no subject.
      // Also cleans up old localStorage key 'preferred-language'.
      const savedSubject = localStorage.getItem('preferred-subject') || localStorage.getItem('preferred-language') || 'python';
      loadPath(savedSubject);
    }

    // Section loading logic can remain similar, but driven by searchParams
    if (sectionFromUrl) {
      loadSection(sectionFromUrl);
    } else {
      // Restore last opened section if available
      const lastOpened = localStorage.getItem('last-opened-section');
      if (lastOpened) {
        loadSection(lastOpened);
      }
    }
    // currentPath is in dependency array to re-evaluate when path is loaded
  }, [subjectFromUrl, sectionFromUrl, currentPath, loadPath, loadSection]);

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

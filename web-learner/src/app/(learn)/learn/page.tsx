'use client';

import { useEffect } from 'react';
import { useLearningStore } from '@/store/learningStore';
import { ContentDisplay } from '@/components/ContentDisplay';

export default function LearnPage() {
  const loadPath = useLearningStore((state) => state.loadPath);
  const loadSection = useLearningStore((state) => state.loadSection);

  useEffect(() => {
    // Get subject from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const urlSubject = (urlParams.get('subject') || urlParams.get('language')) as string | null;
    const savedSubject = (localStorage.getItem('preferred-subject') || localStorage.getItem('preferred-language')) as string | null;
    const finalSubject = urlSubject || savedSubject || 'python';

    // Load course path
    loadPath(finalSubject);

    // Optional deep link to a specific section
    const sectionId = urlParams.get('section');
    if (sectionId) {
      // Directly trigger loading the section markdown
      // This does not depend on path readiness as content is fetched by ID
      loadSection(sectionId);
    } else {
      // Restore last opened section if available
      const lastOpened = localStorage.getItem('last-opened-section');
      if (lastOpened) {
        loadSection(lastOpened);
      }
    }
  }, [loadPath, loadSection]);

  // The layout is now handled by the parent layout.tsx
  // This component is only responsible for displaying the content.
  return <ContentDisplay />;
}

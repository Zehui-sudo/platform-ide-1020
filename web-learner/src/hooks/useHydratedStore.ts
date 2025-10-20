'use client';

import { useEffect, useState } from 'react';
import { useLearningStore } from '@/store/learningStore';

/**
 * Hook to handle hydration of the Zustand store
 * This ensures the store is only accessed on the client side
 */
export function useHydratedStore() {
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // Wait for hydration to complete
    const unsubHydrate = useLearningStore.persist.onHydrate(() => {
      setHydrated(false);
    });

    const unsubFinishHydration = useLearningStore.persist.onFinishHydration(() => {
      setHydrated(true);
    });

    // If already hydrated, set hydrated to true
    if (useLearningStore.persist.hasHydrated()) {
      setHydrated(true);
    }

    return () => {
      unsubHydrate();
      unsubFinishHydration();
    };
  }, []);

  return hydrated;
}
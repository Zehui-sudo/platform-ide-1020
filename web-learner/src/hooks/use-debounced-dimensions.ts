"use client";

import { useState, useEffect, RefObject } from "react";

interface Dimensions {
  width: number;
  height: number;
}

export function useDimensions(ref: RefObject<HTMLElement | SVGElement>): Dimensions {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 0, height: 0 });

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    const updateDimensions = () => {
      if (ref.current) {
        const { width, height } = ref.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    const debouncedUpdateDimensions = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(updateDimensions, 250);
    };

    updateDimensions();
    window.addEventListener("resize", debouncedUpdateDimensions);

    return () => {
      window.removeEventListener("resize", debouncedUpdateDimensions);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [ref]);

  return dimensions;
}


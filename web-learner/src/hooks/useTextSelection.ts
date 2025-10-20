import { useEffect, useCallback } from 'react';
import { useLearningStore } from '@/store/learningStore';
import type { ContextReference } from '@/types';

function getClosestCodeBlock(el: Element | null): HTMLElement | null {
  if (!el) return null;
  let node: Element | null = el;
  while (node) {
    if (node instanceof HTMLElement && node.dataset && node.dataset.role === 'code-block') {
      return node as HTMLElement;
    }
    node = node.parentElement;
  }
  return null;
}

function extractUserCodeFromDom(codeWrapper: HTMLElement): string | null {
  // Try to read the live CodeMirror content
  const cm = codeWrapper.querySelector('.cm-content');
  if (cm) {
    // innerText preserves line breaks
    return (cm as HTMLElement).innerText;
  }
  // Fallback to <pre><code> if present
  const pre = codeWrapper.querySelector('pre');
  if (pre) return (pre as HTMLElement).innerText;
  return null;
}

function clampText(s: string, max = 2500): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + `\n\n...（已截断，剩余 ${s.length - max} 字）`;
}

export function useTextSelection(containerRef: React.RefObject<HTMLElement>) {
  const setSelectedContent = useLearningStore((state) => state.setSelectedContent);
  const currentSection = useLearningStore((state) => state.currentSection);

  const handleSelection = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !containerRef.current) {
      return;
    }

    const selectedText = selection.toString().trim();
    if (!selectedText) {
      return;
    }

    // Check if selection is within our container
    const range = selection.getRangeAt(0);
    const commonAncestor = range.commonAncestorContainer;
    const isWithinContainer = containerRef.current.contains(
      commonAncestor.nodeType === Node.TEXT_NODE 
        ? commonAncestor.parentNode 
        : commonAncestor
    );

    if (!isWithinContainer) {
      return;
    }

    // Determine content type and locate code wrapper if needed
    let contentType: 'markdown' | 'code' = 'markdown';
    let parent = commonAncestor.parentElement;
    let codeWrapper: HTMLElement | null = null;
    while (parent && parent !== containerRef.current) {
      if (parent.classList.contains('cm-editor') || parent.tagName === 'PRE') {
        contentType = 'code';
      }
      if (!codeWrapper) {
        codeWrapper = getClosestCodeBlock(parent);
      }
      parent = parent.parentElement;
    }

    // Get section title as source
    const sectionTitle = currentSection?.id
      .split('-')
      .slice(-1)[0]
      .replace(/-/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());

    // Build enriched context when selection is in code and we can locate the block
    if (contentType === 'code' && codeWrapper) {
      const data = codeWrapper.dataset;
      const sectionId = data.sectionId;
      const markdownIndex = Number(data.markdownIndex ?? '0');
      const startOffset = Number(data.startOffset ?? '-1');
      const language = (data.language || 'javascript') as 'javascript' | 'python';

      const state = useLearningStore.getState();
      const blocks = state.currentSection?.contentBlocks || [];

      // Aggregate markdown prior to current code block
      let prefixMarkdown = '';
      // Sum of markdown lengths for progress estimate
      let totalMarkdownLen = 0;
      let prefixMarkdownLen = 0;
      blocks.forEach((b, idx) => {
        if (b.type === 'markdown') {
          const md = b.content || '';
          if (idx < markdownIndex) {
            prefixMarkdown += md;
            prefixMarkdownLen += md.length;
          }
          totalMarkdownLen += md.length;
          if (idx === markdownIndex && startOffset >= 0) {
            prefixMarkdown += md.slice(0, startOffset);
            prefixMarkdownLen += startOffset;
          }
        }
      });

      // Collect prior code blocks (in DOM order) + current block full
      const allCodeWrappers = Array.from(containerRef.current.querySelectorAll<HTMLElement>('[data-role="code-block"]'));
      const readCodes: Array<{ lang: string; code: string }> = [];
      for (const w of allCodeWrappers) {
        if (w === codeWrapper) {
          // include current full code
          const sid = w.dataset.sectionId || '';
          const live = extractUserCodeFromDom(w);
          const fallback = state.userCodeSnippets[sid] || '';
          const codeText = (live ?? fallback) || '';
          readCodes.push({ lang: w.dataset.language || language, code: codeText });
          break;
        } else {
          // include all prior code blocks
          const sid = w.dataset.sectionId || '';
          const live = extractUserCodeFromDom(w);
          const fallback = state.userCodeSnippets[sid] || '';
          const codeText = (live ?? fallback) || '';
          readCodes.push({ lang: w.dataset.language || 'javascript', code: codeText });
        }
      }

      // Build readSoFar markdown string
      let readSoFar = prefixMarkdown.trim();
      for (const item of readCodes) {
        const lang = (item.lang || '').toLowerCase();
        readSoFar += `\n\n\`\`\`${lang}\n${item.code}\n\`\`\``;
      }
      readSoFar = clampText(readSoFar, 2500);

      const progressPercent = totalMarkdownLen > 0 ? Math.min(100, Math.max(0, Math.round((prefixMarkdownLen / totalMarkdownLen) * 100))) : undefined;

      const contextReference: ContextReference = {
        text: selectedText,
        source: sectionTitle,
        type: contentType,
        blockIndex: Number(codeWrapper.dataset.codeOrdinal || '0'),
        progressPercent,
        readSoFar,
        sectionId: sectionId,
      };

      setSelectedContent(contextReference);
      return;
    }

    // Default: basic context without enrichment
    const contextReference: ContextReference = {
      text: selectedText,
      source: sectionTitle,
      type: contentType,
    };

    setSelectedContent(contextReference);
  }, [containerRef, setSelectedContent, currentSection]);

  // Handle keyboard shortcut
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const isShortcut = isMac ? e.metaKey && e.key === 'l' : e.ctrlKey && e.key === 'l';
    
    if (isShortcut) {
      e.preventDefault();
      handleSelection();
      
      // Focus on chat input
      const chatInput = document.querySelector('[data-chat-input]') as HTMLTextAreaElement;
      if (chatInput) {
        chatInput.focus();
      }
    }
  }, [handleSelection]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Listen for selection changes
    container.addEventListener('mouseup', handleSelection);
    container.addEventListener('keyup', handleSelection);
    
    // Listen for keyboard shortcuts globally
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('mouseup', handleSelection);
      container.removeEventListener('keyup', handleSelection);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleSelection, handleKeyDown, containerRef]);

  return { handleSelection };
}

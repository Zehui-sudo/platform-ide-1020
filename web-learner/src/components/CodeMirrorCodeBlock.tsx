'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { html as cmHtml } from '@codemirror/lang-html';
import { StreamLanguage } from '@codemirror/language';
import type { StreamParser } from '@codemirror/language';
import { EditorView, highlightActiveLine, highlightActiveLineGutter, Decoration } from '@codemirror/view';
import { Compartment, RangeSet, StateEffect, StateField, type Extension } from '@codemirror/state';
import { githubLight, githubDark } from '@uiw/codemirror-theme-github';

// Define effects for search highlighting
const addSearchHighlight = StateEffect.define<RangeSet<Decoration>>();
const clearSearchHighlight = StateEffect.define();

// Create decorations for search highlighting
const searchMatchDecoration = Decoration.mark({
  class: 'cm-searchMatch',
  attributes: { style: 'background-color: var(--accent); color: var(--accent-foreground); border-radius: 2px;' }
});

// Create search highlighting field
const searchHighlightField = StateField.define<RangeSet<Decoration>>({
  create() {
    return Decoration.none;
  },
  update(value, transaction) {
    value = value.map(transaction.changes);
    for (const effect of transaction.effects) {
      if (effect.is(addSearchHighlight)) {
        value = effect.value;
      } else if (effect.is(clearSearchHighlight)) {
        value = Decoration.none;
      }
    }
    return value;
  },
  provide: f => EditorView.decorations.from(f)
});

// Create dynamic styling for active line that respects highlight state
const createDynamicHighlightTheme = (highlightEnabled: boolean) => EditorView.theme({
  '.cm-activeLine': highlightEnabled ? {
    backgroundColor: 'var(--accent)',
  } : {},
  '.cm-activeLineGutter': highlightEnabled ? {
    backgroundColor: 'var(--muted)',
  } : {},
});

type HttpSection = 'requestOrStatus' | 'headers' | 'body';
type HttpHeaderPart = 'name' | 'colon' | 'value';

interface HttpState {
  section: HttpSection;
  headerPart: HttpHeaderPart;
}

const httpMethods = /^(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)\b/;
const httpVersion = /^HTTP\/\d+(?:\.\d+)?/;
const httpStatus = /\b\d{3}\b/;
const httpNumber = /\b\d+(?:\.\d+)?\b/;
const httpString = /"(?:[^"\\]|\\.)*"/;

const httpStreamParser: StreamParser<HttpState> = {
  startState() {
    return {
      section: 'requestOrStatus',
      headerPart: 'name',
    };
  },
  token(stream, state) {
    if (state.section === 'requestOrStatus') {
      if (stream.match(httpMethods)) {
        return 'keyword';
      }
      if (stream.match(httpVersion)) {
        return 'atom';
      }
      if (stream.match(httpStatus)) {
        return 'number';
      }

      stream.next();
      if (stream.eol()) {
        state.section = 'headers';
      }
      return null;
    }

    if (state.section === 'headers') {
      if (stream.sol()) {
        if (stream.match(/^\s*$/)) {
          state.section = 'body';
          return null;
        }
        state.headerPart = 'name';
      }

      if (state.headerPart === 'name') {
        if (stream.eatSpace()) {
          return null;
        }
        const name = stream.match(/[A-Za-z0-9-]+/);
        if (name) {
          if (stream.peek() === ':') {
            state.headerPart = 'colon';
            return 'attributeName';
          }
          return null;
        }
        stream.next();
        return null;
      }

      if (state.headerPart === 'colon') {
        if (stream.match(':')) {
          state.headerPart = 'value';
          return 'punctuation';
        }
        stream.next();
        return null;
      }

      if (state.headerPart === 'value') {
        stream.skipToEnd();
        return 'string';
      }
    }

    if (state.section === 'body') {
      if (stream.match(httpString)) {
        return 'string';
      }
      if (stream.match(httpNumber)) {
        return 'number';
      }
      stream.next();
      return null;
    }

    stream.next();
    return null;
  },
};

const httpLanguage = StreamLanguage.define(httpStreamParser);

interface CodeMirrorCodeBlockProps {
  value: string;
  onChange?: (value: string) => void;
  onBlur?: (value: string) => void;
  language: 'javascript' | 'python' | 'jsx' | 'tsx' | 'html' | 'json' | 'http';
  readOnly?: boolean;
  className?: string;
  searchTerm?: string;
  enableSearch?: boolean;
  fontSize?: number;
  // When true, use transparent backgrounds to fit inside chat bubbles
  transparent?: boolean;
  // Optional: override max height in pixels for the editor viewport
  maxHeightPx?: number;
}

export function CodeMirrorCodeBlock({
  value,
  onChange,
  onBlur,
  language,
  readOnly = false,
  className = '',
  searchTerm = '',
  enableSearch = false,
  fontSize = 14,
  transparent = false,
  maxHeightPx,
}: CodeMirrorCodeBlockProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [highlightCompartment] = useState(new Compartment());
  const [themeCompartment] = useState(new Compartment());
  const highlightIsOn = useRef(true);
  const viewRef = useRef<EditorView | null>(null);

  const languageExtensions = useMemo<Extension[]>(() => {
    switch (language) {
      case 'javascript':
      case 'jsx':
      case 'tsx':
        return [javascript({ jsx: true, typescript: true })];
      case 'json':
        return [javascript()];
      case 'python':
        return [python()];
      case 'html':
        return [cmHtml()];
      case 'http':
        return [httpLanguage];
      default:
        return [];
    }
  }, [language]);

  // Function to find and highlight search matches
  const highlightSearchMatches = (view: EditorView, searchTerm: string) => {
    if (!searchTerm.trim()) {
      view.dispatch({ effects: clearSearchHighlight.of(null) });
      return;
    }

    const doc = view.state.doc;
    const ranges = [];
    const searchRegex = new RegExp(searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');

    for (let i = 1; i <= doc.lines; i++) {
      const line = doc.line(i);
      let match;
      while ((match = searchRegex.exec(line.text)) !== null) {
        const from = line.from + match.index;
        const to = from + match[0].length;
        ranges.push(searchMatchDecoration.range(from, to));
      }
    }

    view.dispatch({
      effects: addSearchHighlight.of(RangeSet.of(ranges, true))
    });
  };

  const dynamicHighlightExtension = EditorView.updateListener.of((update) => {
    if (update.selectionSet) {
      const isSelectionEmpty = update.state.selection.main.empty;
      const hasSearchMatches = searchTerm && searchTerm.trim().length > 0;

      // Only disable line highlighting when there's actual text selection AND no search matches
      if (!isSelectionEmpty && highlightIsOn.current && !hasSearchMatches) {
        highlightIsOn.current = false;
        update.view.dispatch({
          effects: [
            highlightCompartment.reconfigure([]),
            themeCompartment.reconfigure(createDynamicHighlightTheme(false))
          ]
        });
      } else if ((isSelectionEmpty || hasSearchMatches) && !highlightIsOn.current) {
        // Re-enable line highlighting when:
        // 1. Selection is empty (cursor only), OR
        // 2. There are search matches active
        highlightIsOn.current = true;
        update.view.dispatch({
          effects: [
            highlightCompartment.reconfigure([highlightActiveLine(), highlightActiveLineGutter()]),
            themeCompartment.reconfigure(createDynamicHighlightTheme(true))
          ]
        });
      }
    }
  });

  useEffect(() => {
    const checkTheme = () => {
      const isDarkMode = document.documentElement.classList.contains('dark');
      setTheme(isDarkMode ? 'dark' : 'light');
    };
    checkTheme();
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Effect to handle search highlighting changes
  useEffect(() => {
    if (viewRef.current && enableSearch) {
      highlightSearchMatches(viewRef.current, searchTerm);
    }
  }, [searchTerm, enableSearch]);

  // Effect to handle value changes and re-apply search highlighting
  useEffect(() => {
    if (viewRef.current && enableSearch && searchTerm) {
      setTimeout(() => {
        highlightSearchMatches(viewRef.current!, searchTerm);
      }, 50);
    }
  }, [value, enableSearch, searchTerm]);

  // Base theme depending on transparency
  const baseTheme = EditorView.theme({
    '&': {
      backgroundColor: transparent ? 'transparent' : 'var(--background) !important',
      color: 'var(--foreground)',
    },
    '.cm-gutters': {
      backgroundColor: transparent ? 'transparent' : 'var(--background) !important',
      borderRight: transparent ? 'none' : '1px solid var(--border)',
    },
    '.cm-searchMatch': {
      backgroundColor: 'var(--accent)',
      color: 'var(--accent-foreground)',
      borderRadius: '2px',
      padding: '1px 2px',
    },
  });

  return (
    <div 
      className={`border rounded-md overflow-hidden ${transparent ? 'bg-transparent' : 'bg-background'} ${className}`}
    >
      <CodeMirror
        value={value}
        maxHeight={typeof maxHeightPx === 'number' ? `${maxHeightPx}px` : '200px'}
        extensions={[
          theme === 'light' ? githubLight : githubDark,
          baseTheme,
          EditorView.theme({
            '&': { fontSize: `${fontSize}px` },
            '.cm-content': { fontSize: `${fontSize}px` },
            '.cm-gutters': { fontSize: `${fontSize}px` },
          }),
          ...languageExtensions,
          EditorView.lineWrapping,
          searchHighlightField,
          highlightCompartment.of([highlightActiveLine(), highlightActiveLineGutter()]),
          themeCompartment.of(createDynamicHighlightTheme(true)),
          dynamicHighlightExtension,
        ]}
        onChange={onChange}
        onBlur={onBlur ? () => onBlur(viewRef.current?.state.doc.toString() ?? value) : undefined}
        readOnly={readOnly}
        onCreateEditor={(view) => {
          viewRef.current = view;
          if (enableSearch && searchTerm) {
            setTimeout(() => {
              highlightSearchMatches(view, searchTerm);
            }, 100);
          }
        }}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          dropCursor: true,
          allowMultipleSelections: false,
          indentOnInput: true,
          bracketMatching: true,
          closeBrackets: true,
          autocompletion: true,
          rectangularSelection: false,
          crosshairCursor: false,
          highlightSelectionMatches: true,
          searchKeymap: false,
        }}
        style={{
          fontSize: '14px',
        }}
      />
    </div>
  );
}

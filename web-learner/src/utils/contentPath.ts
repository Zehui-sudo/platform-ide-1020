/**
 * Content path utilities for nested topic-based content structure.
 * - Languages (topics): 'python' | 'javascript' | 'astrology' | 'langgraph'
 * - New path shape: /content/{language}/{filename}.md
 *
 * Backward compatibility:
 * - Accept legacy flat sectionId like "js-sec-..." | "py-sec-..." | "astro-sec-..." | "astrology_index" | "lg-sec-..."
 * - Accept legacy python ids "python-sec-..." and map them to "py-sec-..." files.
 */

export type Language = string; // dynamic languages discovered from /public/content

/**
 * Ensure a filename has .md suffix exactly once.
 */
function ensureMdExt(filename: string): string {
  const clean = filename.trim().replace(/^\/+/, '');
  return clean.endsWith('.md') ? clean : `${clean}.md`;
}

/**
 * Infer language(topic) from section id filename prefix.
 */
function inferLanguageFromId(sectionId: string): Language {
  if (sectionId.startsWith('py-')) return 'python';
  if (sectionId.startsWith('js-')) return 'javascript';
  if (sectionId.startsWith('lg-')) return 'langgraph';
  // Astrology content conventions
  if (sectionId === 'astrology_index') return 'astrology';
  if (sectionId.startsWith('astro-')) return 'astrology';
  // Default fallback: javascript (least surprising for web course),
  // but downstream fetch errors will still be handled gracefully.
  return 'javascript';
}

/**
 * Normalize legacy section id to the actual filename used on disk.
 * - Strips ".md" if present
 * - Maps "python-sec-*" to "py-sec-*"
 */
function normalizeLegacyFilename(legacySectionId: string): string {
  // Strip md suffix if present
  let id = legacySectionId.trim().replace(/\.md$/i, '');

  // Special compatibility: python "python-sec-*" → "py-sec-*"
  if (id.startsWith('python-sec-')) {
    id = id.replace(/^python-sec-/, 'py-sec-');
  }

  return id;
}

/**
 * Build nested content path for the given language + filename.
 * Returns a public URL starting with "/content/...".
 */
export function getContentPath(language: Language, filename: string): string {
  const file = ensureMdExt(filename);
  return `/content/${language}/${file}`;
}

/**
 * Resolve a legacy flat section id (e.g., "js-sec-1-2-3-...") to
 * - language (topic folder)
 * - filename (md file name without path, may omit .md on input)
 *
 * Backward-compat rules:
 * - py-*, js-*, astro-*, lg-* map to python/javascript/astrology/langgraph respectively
 * - python-sec-* is rewritten to py-sec-* (actual filename)
 * - "astrology_index" belongs to astrology
 */
export function resolveLegacyPath(legacySectionId: string): { language: Language; filename: string } {
  const normalized = normalizeLegacyFilename(legacySectionId);
  const language = inferLanguageFromId(normalized);
  // The physical file name equals normalized id (plus .md appended by getContentPath)
  return {
    language,
    filename: normalized,
  };
}

/**
 * Optional helper: direct resolve to nested URL from legacy id.
 * Keeps the filename transform logic in one place.
 */
export function resolveLegacyUrl(legacySectionId: string): string {
  const { language, filename } = resolveLegacyPath(legacySectionId);
  return getContentPath(language, filename);
}

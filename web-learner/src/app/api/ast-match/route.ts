import { NextRequest } from 'next/server';

export const runtime = 'edge';

type Language = 'javascript' | 'python';

type AstFeatures = {
  atomic: { syntax: string[]; api: string[]; operations: string[] };
  structural: { patterns: string[]; nesting: number; complexity: number };
  statistical: {
    syntaxDistribution: { basic: string[]; intermediate: string[]; advanced: string[] };
    featureCount: { basicCount: number; intermediateCount: number; advancedCount: number };
  };
};

type IndexEntry = {
  id: string;
  title: string;
  language: Language;
  features: Record<string, number>;
  required: string[];
};

type AstMatchItem = {
  sectionId: string;
  title: string;
  language: Language;
  score: number;
  url: string;
};

function buildDeepLink(sectionId: string, language: Language): string {
  return `/learn?language=${language}&section=${encodeURIComponent(sectionId)}`;
}

function featureMatches(required: string, features: Set<string>): boolean {
  if (features.has(required)) return true;
  // Strict fuzzy synonyms, avoid broad substring matches
  const FUZZY: Record<string, string[]> = {
    'array-method': ['Array.map', '.map', 'Array.filter', '.filter', 'Array.reduce', '.reduce'],
    'promise': ['Promise', 'Promise.all', 'Promise.race', '.then', '.catch'],
    'async': ['async', 'async-await', 'async-function'],
    'await': ['await'],
    'try-catch': ['try', 'catch', 'try-catch-finally'],
    'arrow-function': ['=>', 'arrow-function'],
    'import': ['import', 'export', 'default-export', 'named-export'],
    'dynamic-import': ['import('],
    'spread': ['rest', '...'],
    'destructuring': ['object-destructuring', 'array-destructuring'],
    'for-loop': ['for-of', 'for-in'],
    'conditional': ['switch'],
    };
  const alts = FUZZY[required];
  if (alts) {
    for (const a of alts) {
      if (features.has(a)) return true;
    }
  }
  return false;
}

// Heuristic: determine core features that must be present for a section
function getCoreForSection(entry: IndexEntry): string[] {
  const id = entry.id || '';
  const title = entry.title || '';
  // Dynamic import
  if (id.includes('7-2-4') || title.includes('动态导入')) return ['dynamic-import', 'import(' as unknown as string];
  // Fetch basics
  if (id.includes('8-1-1') || title.includes('fetch基础')) return ['fetch'];
  // Response handling
  if (id.includes('8-1-3') || title.includes('响应处理')) return ['.json(' as unknown as string, 'json'];
  // Concurrency control
  if (id.includes('5-3-4') || title.includes('并发控制')) return ['Promise.all', 'Promise.race'];
  // Event listening
  if (title.includes('事件监听') || id.includes('6-2-1')) return ['addEventListener'];
  // Array transformation
  if (title.includes('数组转换') || id.includes('2-1-4')) return ['array-method', '.map', '.filter', '.reduce'];
  // Async/await section
  if (id.includes('5-3-1') || id.includes('5-3-2') || title.includes('async') || title.includes('await')) return ['async', 'await', 'async-await'];
  // Default: no hard core
  return [];
}

// Generic features with reduced weight
function isGenericFeature(feat: string): boolean {
  const generic = new Set([
    'async','await','async-await','try-catch','conditional','for-loop','arrow-function',
    'assignment','binary-operator','unary-operator','return','new','switch','break','continue'
  ]);
  return generic.has(feat);
}

function scoreAgainstIndex(
  entry: IndexEntry,
  incoming: AstFeatures,
  language?: Language
): number {
  if (language && entry.language !== language) return 0;

  const incomingSet = new Set<string>([
    ...incoming.atomic.syntax,
    ...incoming.atomic.api,
    ...incoming.atomic.operations,
    ...incoming.structural.patterns,
  ]);

  // Core gating: certain sections require at least one core feature
  const core = getCoreForSection(entry);
  if (core.length > 0) {
    const coreHit = core.some(c => featureMatches(c, incomingSet));
    if (!coreHit) return 0;
  }

  if (entry.required && entry.required.length > 0) {
    const hits = entry.required.filter(r => featureMatches(r, incomingSet)).length;
    if (hits / entry.required.length < 0.5) return 0;
  }

  let score = 0;
  for (const [feat, weight] of Object.entries(entry.features)) {
    if (featureMatches(feat, incomingSet)) {
      const factor = isGenericFeature(feat) ? 0.35 : 1.0;
      score += weight * factor;
    }
  }

  // Light adjustment by complexity (favor advanced-like content)
  if (incoming.structural.complexity > 5) {
    score *= 1.05;
  }

  return score;
}

async function loadAstIndex(req: NextRequest): Promise<IndexEntry[]> {
  const url = new URL('/ast-index.json', req.nextUrl.origin);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`ast-index.json not found (${res.status})`);
  const json = await res.json();
  return Array.isArray(json.sections) ? json.sections as IndexEntry[] : [];
}

function corsHeaders() {
  return {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  } as Record<string, string>;
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { features, language } = body as { features: AstFeatures; language?: Language };

    if (!features || typeof features !== 'object') {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid or missing features payload' }), {
        status: 400,
        headers: corsHeaders(),
      });
    }

    const index = await loadAstIndex(req);
    if (!index || index.length === 0) {
      return new Response(JSON.stringify({ ok: false, error: 'AST index is empty' }), {
        status: 500,
        headers: corsHeaders(),
      });
    }

    const scored: Array<{ entry: IndexEntry; score: number }> = index
      .map(entry => ({ entry, score: scoreAgainstIndex(entry, features, language) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);

    const matches: AstMatchItem[] = scored.map(x => ({
      sectionId: x.entry.id,
      title: x.entry.title,
      language: x.entry.language,
      // slightly stricter normalization to reduce 100% saturation
      score: Math.min(x.score / 4.0, 1),
      url: buildDeepLink(x.entry.id, x.entry.language),
    }));

    const primary = matches[0]?.sectionId || null;
    return new Response(JSON.stringify({ ok: true, primary, matches }), {
      status: 200,
      headers: corsHeaders(),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ ok: false, error: message }), {
      status: 500,
      headers: corsHeaders(),
    });
  }
}

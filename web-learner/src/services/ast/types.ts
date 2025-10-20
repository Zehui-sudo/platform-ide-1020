export interface AtomicFeatures {
  syntax: string[];
  api: string[];
  operations: string[];
}

export interface StructuralFeatures {
  patterns: string[];
  nesting: number;
  complexity: number;
}

export interface StatisticalFeatures {
  syntaxDistribution: {
    basic: string[];
    intermediate: string[];
    advanced: string[];
  };
  featureCount: {
    basicCount: number;
    intermediateCount: number;
    advancedCount: number;
  };
}

export interface AstFeatures {
  atomic: AtomicFeatures;
  structural: StructuralFeatures;
  statistical: StatisticalFeatures;
}

export interface KnowledgeDefinition {
  id: string; // e.g. js-sec-2-1-4
  title: string;
  requiredFeatures: string[];
  optionalFeatures: string[];
  weight: Map<string, number>;
  difficulty: 'basic' | 'intermediate' | 'advanced';
  dependencies?: string[];
  category: string;
}

export interface AstMatchItem {
  sectionId: string;
  title: string;
  language: 'javascript' | 'python';
  score: number; // raw score
  url: string;   // deep link
}

export interface AstMatchResponse {
  ok: true;
  primary: string | null;
  matches: AstMatchItem[];
}

export interface AstMatchErrorResponse {
  ok: false;
  error: string;
}


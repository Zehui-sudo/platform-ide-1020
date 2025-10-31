import type { LearningConfigSnapshot } from '@/types';

export type GeneratedSubjectResult = {
  subjectSlug: string;
  label: string;
  relativeJsonPath: string;
  parsed: unknown;
  targetFile: string;
};

export type ResolvedPaths = {
  projectRoot: string;
  publicDir: string;
  contentRoot: string;
  outputRoot: string;
};

export function resolvePaths(projectRoot?: string): ResolvedPaths;

export function readLearningConfig(
  outputRoot: string,
): Promise<LearningConfigSnapshot | null>;

export function writeLearningConfig(
  outputRoot: string,
  config: LearningConfigSnapshot,
): Promise<void>;

export function generateSubjectLearnData(options: {
  projectRoot?: string;
  contentRoot?: string;
  outputRoot?: string;
  subjectSlug: string;
  logger?: Console;
}): Promise<GeneratedSubjectResult | null>;

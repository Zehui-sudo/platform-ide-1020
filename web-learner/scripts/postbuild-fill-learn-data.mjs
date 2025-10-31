#!/usr/bin/env node
import path from 'path';
import { fileURLToPath } from 'url';
import {
  generateSubjectLearnData,
  readLearningConfig,
  writeLearningConfig,
  resolvePaths,
  discoverSubjectSlugs,
} from './generate-learn-data.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI_TAG = '[postbuild-fill-learn-data]';

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const paths = resolvePaths(projectRoot);

  const existingConfig =
    (await readLearningConfig(paths.outputRoot)) ?? {
      generatedAt: new Date().toISOString(),
      subjects: [],
      pathMap: {},
      labelMap: {},
    };

  const currentSubjects = new Set(existingConfig.subjects ?? []);
  const availableSlugs = await discoverSubjectSlugs(paths.contentRoot);
  const missingSlugs = availableSlugs.filter((slug) => !currentSubjects.has(slug));

  if (missingSlugs.length === 0) {
    console.log(`${CLI_TAG} 没有新增课程，无需补齐`);
    return;
  }

  const pathMap = { ...(existingConfig.pathMap ?? {}) };
  const labelMap = { ...(existingConfig.labelMap ?? {}) };
  const created = [];

  for (const slug of missingSlugs) {
    const result = await generateSubjectLearnData({
      projectRoot,
      contentRoot: paths.contentRoot,
      outputRoot: paths.outputRoot,
      subjectSlug: slug,
      logger: console,
    });

    if (!result) {
      continue;
    }

    created.push(slug);
    pathMap[slug] = result.relativeJsonPath;
    labelMap[slug] = result.label;
  }

  if (created.length === 0) {
    console.log(`${CLI_TAG} 新增课程目录存在，但缺少有效的 learning-path.md`);
    return;
  }

  const mergedSubjects = Array.from(new Set([...(existingConfig.subjects ?? []), ...created]));
  mergedSubjects.sort((a, b) => a.localeCompare(b));

  const nextConfig = {
    ...existingConfig,
    generatedAt: new Date().toISOString(),
    subjects: mergedSubjects,
    pathMap,
    labelMap,
  };

  await writeLearningConfig(paths.outputRoot, nextConfig);

  console.log(`${CLI_TAG} 已补齐 ${created.length} 门课程: ${created.join(', ')}`);
}

main().catch((error) => {
  console.error(`${CLI_TAG} 执行失败:`, error);
  process.exitCode = 1;
});

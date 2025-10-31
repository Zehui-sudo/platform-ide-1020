#!/usr/bin/env node
import fsp from 'fs/promises';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI_TAG = '[generate-learn-data]';
const idRegex = /\(id:\s*([^)]+)\)/i;

export const cleanTitle = (input) => {
  if (!input) return '';

  let title = input
    .replace(/\(id:\s*[^)]+\)/gi, '')
    .replace(/（[^）]*）/g, '')
    .replace(/\([^)]*\)/g, '')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/\s*[：:]\s*/g, '：')
    .replace(/\s+/g, ' ')
    .trim();

  const prefixPatterns = [
    /^第[\d０-９一二三四五六七八九十百千万〇零两]+[章节节篇部分卷]\s*[：:]\s*/,
    /^第[\d０-９一二三四五六七八九十百千万〇零两]+[章节节篇部分卷]\s*/,
    /^\d+(?:\.\d+)*\s*[：:．。]?\s*/,
  ];

  let previous;
  do {
    previous = title;
    prefixPatterns.forEach((pattern) => {
      title = title.replace(pattern, '');
    });
    title = title.replace(/^[：:]/, '').trim();
  } while (title !== previous);

  title = title.replace(/([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])/g, '$1$2');

  return title.trim();
};

const normalizeForComparison = (input) => cleanTitle(input).replace(/\s+/g, '').toLowerCase();

const ensureArray = (value) => (Array.isArray(value) ? value : []);

export const parseLearningPath = (markdown, subjectSlug) => {
  const lines = markdown.split(/\r?\n/);
  const learningPath = {
    id: '',
    title: subjectSlug,
    subject: subjectSlug,
    chapters: [],
  };

  const pathLine = lines.find((line) => line.trim().startsWith('# '));
  if (pathLine) {
    const trimmed = pathLine.trim();
    const title = trimmed.replace(/^#\s*/, '').replace(idRegex, '').trim();
    learningPath.title = cleanTitle(title) || subjectSlug;
    const match = trimmed.match(idRegex);
    if (match) {
      learningPath.id = match[1];
    }
  } else {
    learningPath.title = cleanTitle(learningPath.title) || subjectSlug;
  }

  let currentChapter = null;
  let currentGroup = null;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    if (line.startsWith('## ')) {
      const match = line.match(idRegex);
      const rawTitle = line.replace(/^##\s*/, '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      if (!match) {
        console.warn(`${CLI_TAG} 章节缺少 id: ${subjectSlug} -> ${line}`);
        continue;
      }
      currentChapter = {
        id: match[1],
        title,
        groups: [],
        sections: [],
      };
      learningPath.chapters.push(currentChapter);
      currentGroup = null;
    } else if (line.startsWith('### ') && currentChapter) {
      const match = line.match(idRegex);
      const rawTitle = line.replace(/^###\s*/, '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      if (!match) {
        console.warn(`${CLI_TAG} 小节分组缺少 id: ${subjectSlug} -> ${line}`);
        continue;
      }
      currentGroup = {
        id: match[1],
        title,
        sections: [],
      };
      currentChapter.groups = ensureArray(currentChapter.groups);
      currentChapter.groups.push(currentGroup);
    } else if (line.startsWith('#### ') && currentChapter) {
      const match = line.match(idRegex);
      const rawTitle = line.replace(/^####\s*/, '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      if (!match) {
        console.warn(`${CLI_TAG} 节缺少 id: ${subjectSlug} -> ${line}`);
        continue;
      }
      const section = {
        id: match[1],
        title,
        chapterId: currentChapter.id,
      };
      if (currentGroup) {
        currentGroup.sections = ensureArray(currentGroup.sections);
        currentGroup.sections.push(section);
      } else {
        currentChapter.sections = ensureArray(currentChapter.sections);
        currentChapter.sections.push(section);
      }
    }
  }

  learningPath.chapters = learningPath.chapters.map((chapter, index) => {
    let groups = ensureArray(chapter.groups).map((g) => ({
      ...g,
      sections: ensureArray(g.sections),
    }));
    let sections = ensureArray(chapter.sections);

    if (groups.length === 1) {
      const [group] = groups;
      if (normalizeForComparison(group.title) === normalizeForComparison(chapter.title)) {
        sections = [...sections, ...group.sections];
        groups = [];
      }
    }

    return {
      ...chapter,
      title: `第${index + 1}章：${chapter.title}`,
      groups,
      sections,
    };
  });

  return learningPath;
};

export const resolvePaths = (projectRoot) => {
  const root = projectRoot ?? path.resolve(__dirname, '..');
  const publicDir = path.join(root, 'public');
  return {
    projectRoot: root,
    publicDir,
    contentRoot: path.join(publicDir, 'content'),
    outputRoot: path.join(publicDir, 'learn-data'),
  };
};

export const discoverSubjectSlugs = async (contentRoot) => {
  try {
    const entries = await fsp.readdir(contentRoot, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
      .map((entry) => entry.name);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return [];
    }
    throw error;
  }
};

export async function removeStaleJsonFiles(dir) {
  try {
    const entries = await fsp.readdir(dir, { withFileTypes: true });
    await Promise.all(
      entries.map(async (entry) => {
        if (entry.isFile() && entry.name.endsWith('.json')) {
          await fsp.unlink(path.join(dir, entry.name));
        }
      }),
    );
  } catch (error) {
    if (!(error && error.code === 'ENOENT')) {
      throw error;
    }
  }
}

const learningConfigPath = (outputRoot) => path.join(outputRoot, 'learning-config.json');

export const readLearningConfig = async (outputRoot) => {
  try {
    const raw = await fsp.readFile(learningConfigPath(outputRoot), 'utf8');
    return JSON.parse(raw);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
};

export const writeLearningConfig = async (outputRoot, config) => {
  await fsp.writeFile(
    learningConfigPath(outputRoot),
    JSON.stringify(config, null, 2),
    'utf8',
  );
};

export async function generateSubjectLearnData({
  projectRoot,
  contentRoot,
  outputRoot,
  subjectSlug,
  logger = console,
} = {}) {
  if (!subjectSlug) {
    throw new Error('generateSubjectLearnData: subjectSlug is required');
  }

  const paths = resolvePaths(projectRoot);
  const contentDir = contentRoot ?? paths.contentRoot;
  const outputDir = outputRoot ?? paths.outputRoot;
  const subjectDir = path.join(contentDir, subjectSlug);

  let stat;
  try {
    stat = await fsp.stat(subjectDir);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      logger.warn(`${CLI_TAG} 未找到课程目录: ${subjectSlug}`);
      return null;
    }
    throw error;
  }

  if (!stat.isDirectory()) {
    logger.warn(`${CLI_TAG} 目标不是有效课程目录: ${subjectSlug}`);
    return null;
  }

  const files = await fsp.readdir(subjectDir);
  const learningPathFile = files.find((file) => file.endsWith('learning-path.md'));

  if (!learningPathFile) {
    logger.warn(`${CLI_TAG} 未找到学习路径文件: ${subjectSlug}`);
    return null;
  }

  const markdown = await fsp.readFile(path.join(subjectDir, learningPathFile), 'utf8');
  const parsed = parseLearningPath(markdown, subjectSlug);
  const label = parsed.title || subjectSlug;
  const relativeJsonPath = `/learn-data/${subjectSlug}.json`;
  const targetFile = path.join(outputDir, `${subjectSlug}.json`);

  await fsp.mkdir(outputDir, { recursive: true });
  await fsp.writeFile(targetFile, JSON.stringify(parsed, null, 2), 'utf8');

  return {
    subjectSlug,
    label,
    relativeJsonPath,
    parsed,
    targetFile,
  };
}

export async function generateLearnData({
  projectRoot,
  subjectSlugs,
  cleanOutput,
  logger = console,
  skipConfig = false,
} = {}) {
  const paths = resolvePaths(projectRoot);
  await fsp.mkdir(paths.outputRoot, { recursive: true });

  const uniqueSubjects = subjectSlugs
    ? Array.from(new Set(subjectSlugs.filter(Boolean)))
    : null;
  const subjects =
    uniqueSubjects && uniqueSubjects.length > 0
      ? uniqueSubjects
      : await discoverSubjectSlugs(paths.contentRoot);
  const isPartial = Boolean(uniqueSubjects && uniqueSubjects.length > 0);

  const shouldClean =
    typeof cleanOutput === 'boolean'
      ? cleanOutput
      : subjects.length > 0 && (!uniqueSubjects || uniqueSubjects.length === 0);

  if (shouldClean) {
    await removeStaleJsonFiles(paths.outputRoot);
  }

  const processed = [];
  const skipped = [];
  const pathMap = {};
  const labelMap = {};
  let firstError = null;

  for (const subjectSlug of subjects) {
    try {
      const result = await generateSubjectLearnData({
        projectRoot: paths.projectRoot,
        contentRoot: paths.contentRoot,
        outputRoot: paths.outputRoot,
        subjectSlug,
        logger,
      });
      if (!result) {
        skipped.push(subjectSlug);
        continue;
      }
      processed.push(subjectSlug);
      pathMap[subjectSlug] = result.relativeJsonPath;
      labelMap[subjectSlug] = result.label;
    } catch (error) {
      skipped.push(subjectSlug);
      if (!firstError) {
        firstError = error;
      }
      logger.error?.(`${CLI_TAG} 生成课程数据失败: ${subjectSlug}`, error);
    }
  }

  const sortedProcessed = [...processed].sort((a, b) => a.localeCompare(b));
  let config = {
    generatedAt: new Date().toISOString(),
    subjects: sortedProcessed,
    pathMap,
    labelMap,
  };

  if (isPartial) {
    const existingConfig = await readLearningConfig(paths.outputRoot);
    if (existingConfig) {
      if (sortedProcessed.length === 0) {
        config = existingConfig;
      } else {
        const mergedSubjects = Array.from(
          new Set([...(existingConfig.subjects ?? []), ...sortedProcessed]),
        ).sort((a, b) => a.localeCompare(b));
        config = {
          generatedAt: new Date().toISOString(),
          subjects: mergedSubjects,
          pathMap: { ...(existingConfig.pathMap ?? {}), ...pathMap },
          labelMap: { ...(existingConfig.labelMap ?? {}), ...labelMap },
        };
      }
    }
  }

  const shouldWriteConfig =
    !skipConfig && (!isPartial || sortedProcessed.length > 0);

  if (shouldWriteConfig) {
    await writeLearningConfig(paths.outputRoot, config);
  }

  if (firstError) {
    throw firstError;
  }

  return {
    config,
    processedSubjects: sortedProcessed,
    skippedSubjects: skipped,
    paths,
  };
}

const parseCliArgs = (argv) => {
  const args = argv.slice(2);
  const options = {};

  for (const raw of args) {
    if (!raw) continue;
    if (raw === '--help' || raw === '-h') {
      options.help = true;
    } else if (raw === '--clean') {
      options.cleanOutput = true;
    } else if (raw === '--no-clean') {
      options.cleanOutput = false;
    } else if (raw.startsWith('--subjects=')) {
      const list = raw.slice('--subjects='.length);
      options.subjectSlugs = list
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
    } else {
      throw new Error(`未知参数: ${raw}`);
    }
  }

  return options;
};

const printHelp = () => {
  console.log(`Usage: node scripts/generate-learn-data.mjs [options]

Options:
  --subjects=slug1,slug2  仅生成指定科目的数据
  --clean                 在生成前清空输出目录
  --no-clean              保留已有输出文件
  -h, --help              显示帮助

默认情况下，当未指定 --subjects 时会清空输出目录。若指定了 --subjects 默认不会清空，可通过 --clean 强制清空。`);
};

const isCliEntry = () => {
  if (!process.argv?.[1]) return false;
  try {
    return pathToFileURL(process.argv[1]).href === import.meta.url;
  } catch {
    return false;
  }
};

async function main() {
  try {
    const cliOptions = parseCliArgs(process.argv);
    if (cliOptions.help) {
      printHelp();
      return;
    }

    const start = Date.now();
    const shouldClean =
      typeof cliOptions.cleanOutput === 'boolean'
        ? cliOptions.cleanOutput
        : !(cliOptions.subjectSlugs && cliOptions.subjectSlugs.length > 0);

    const { processedSubjects } = await generateLearnData({
      projectRoot: path.resolve(__dirname, '..'),
      subjectSlugs: cliOptions.subjectSlugs,
      cleanOutput: shouldClean,
      logger: console,
    });

    const duration = Date.now() - start;
    console.log(
      `${CLI_TAG} 生成完成：${processedSubjects.length} 门课程，耗时 ${duration}ms`,
    );
  } catch (error) {
    console.error(`${CLI_TAG} 生成失败:`, error);
    process.exitCode = 1;
  }
}

if (isCliEntry()) {
  main();
}

#!/usr/bin/env node
import fsp from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const publicDir = path.join(projectRoot, 'public');
const contentRoot = path.join(publicDir, 'content');
const outputRoot = path.join(publicDir, 'learn-data');

const idRegex = /\(id:\s*([^)]+)\)/i;

const cleanTitle = (input) => {
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

function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

function parseLearningPath(markdown, subjectSlug) {
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
        console.warn(`[generate-learn-data] 章节缺少 id: ${subjectSlug} -> ${line}`);
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
        console.warn(`[generate-learn-data] 小节分组缺少 id: ${subjectSlug} -> ${line}`);
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
        console.warn(`[generate-learn-data] 节缺少 id: ${subjectSlug} -> ${line}`);
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
}

async function removeStaleJsonFiles(dir) {
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
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

async function main() {
  try {
    const start = Date.now();
    await fsp.mkdir(outputRoot, { recursive: true });
    await removeStaleJsonFiles(outputRoot);

    const subjects = [];
    const pathMap = {};
    const labelMap = {};

    const entries = await fsp.readdir(contentRoot, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('.')) continue;

      const subjectSlug = entry.name;
      const subjectDir = path.join(contentRoot, subjectSlug);
      const files = await fsp.readdir(subjectDir);
      const learningPathFile = files.find((file) => file.endsWith('learning-path.md'));
      if (!learningPathFile) {
        console.warn(`[generate-learn-data] 未找到学习路径文件: ${subjectSlug}`);
        continue;
      }

      const markdown = await fsp.readFile(path.join(subjectDir, learningPathFile), 'utf8');
      const parsed = parseLearningPath(markdown, subjectSlug);
      const label = parsed.title || subjectSlug;
      const relativeJsonPath = `/learn-data/${subjectSlug}.json`;

      await fsp.writeFile(path.join(outputRoot, `${subjectSlug}.json`), JSON.stringify(parsed, null, 2), 'utf8');

      subjects.push(subjectSlug);
      pathMap[subjectSlug] = relativeJsonPath;
      labelMap[subjectSlug] = label;
    }

    subjects.sort((a, b) => a.localeCompare(b));

    const config = {
      generatedAt: new Date().toISOString(),
      subjects,
      pathMap,
      labelMap,
    };

    await fsp.writeFile(path.join(outputRoot, 'learning-config.json'), JSON.stringify(config, null, 2), 'utf8');

    const duration = Date.now() - start;
    console.log(`[generate-learn-data] 生成完成：${subjects.length} 门课程，耗时 ${duration}ms`);
  } catch (error) {
    console.error('[generate-learn-data] 生成失败:', error);
    process.exitCode = 1;
  }
}

main();

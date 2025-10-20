import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  const publicDir = path.join(process.cwd(), 'public');
  const contentRoot = path.join(publicDir, 'content');

  const subjects: string[] = [];
  const pathMap: Record<string, string | null> = Object.create(null);
  const iconMap: Record<string, string> = Object.create(null);
  const labelMap: Record<string, string> = Object.create(null);

  // Helper function to find learning path file for a language
  const findLearningPathForLanguage = (lang: string): { publicPath: string; absPath: string } | null => {
    // First try to find in content subdirectory
    const contentPathFile = path.join(contentRoot, lang, `${lang}-learning-path.md`);
    if (fs.existsSync(contentPathFile)) {
      return { publicPath: `/content/${lang}/${lang}-learning-path.md`, absPath: contentPathFile };
    }

    // Fallback to public root directory
    const publicPathFile = path.join(publicDir, `${lang}-learning-path.md`);
    if (fs.existsSync(publicPathFile)) {
      return { publicPath: `/${lang}-learning-path.md`, absPath: publicPathFile };
    }

    return null;
  };

  // Helper function to find icon for a language
  const findIconForLanguage = (lang: string): string => {
    const iconExtensions = ['.svg', '.png'];
    const iconNames = [
      `${lang}-logo`,
      `${lang}-icon`,
      `${lang}`,
      lang
    ];

    // First try to find in content subdirectory
    for (const iconName of iconNames) {
      for (const ext of iconExtensions) {
        const iconPath = path.join(contentRoot, lang, `${iconName}${ext}`);
        if (fs.existsSync(iconPath)) {
          return `/content/${lang}/${iconName}${ext}`;
        }
      }
    }

    // Fallback to public root directory
    for (const iconName of iconNames) {
      for (const ext of iconExtensions) {
        const iconPath = path.join(publicDir, `${iconName}${ext}`);
        if (fs.existsSync(iconPath)) {
          return `/${iconName}${ext}`;
        }
      }
    }

    // Final fallback to default icon
    return '/course_icon.svg';
  };

  try {
    const entries = fs.readdirSync(contentRoot, { withFileTypes: true });
    for (const e of entries) {
      if (e.isDirectory()) {
        const lang = e.name;
        if (lang.startsWith('.')) continue;

        // Find learning path file for this language
        const learningPathInfo = findLearningPathForLanguage(lang);

        if (learningPathInfo) {
          subjects.push(lang);
          pathMap[lang] = learningPathInfo.publicPath;
          // Find icon for this language
          iconMap[lang] = findIconForLanguage(lang);
          // Derive human-readable label from the first H1 in the learning path
          try {
            const md = fs.readFileSync(learningPathInfo.absPath, 'utf8');
            const firstH1 = md.split('\n').find((line) => line.startsWith('# '));
            if (firstH1) {
              const title = firstH1
                .replace(/^#\s+/, '')
                .replace(/\(id:\s*[^)]+\)/i, '')
                .trim();
              if (title) labelMap[lang] = title;
            }
          } catch {}
        } else {
          pathMap[lang] = null;
          iconMap[lang] = '/course_icon.svg';
        }
      }
    }
  } catch {
    // ignore and return empty list
  }

  return NextResponse.json({ subjects, pathMap, iconMap, labelMap });
}

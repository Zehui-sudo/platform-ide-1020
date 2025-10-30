import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { LearningState, LearningActions, LearningPath, SectionContent, ChatMessage, ChatSession, ContextReference, AIProviderType, Chapter, SectionLink, Section } from '@/types';
import { getKnowledgeLinkService } from '@/services/knowledgeLinkService';
// contentPath legacy helpers are no longer used for section resolution

const cleanTitle = (input: string): string => {
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

  let previous: string;
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

const normalizeForComparison = (input: string): string =>
  cleanTitle(input).replace(/\s+/g, '').toLowerCase();

type LearningConfig = {
  subjects: string[];
  pathMap?: Partial<Record<string, string | null>>;
  labelMap?: Record<string, string>;
};

const learningConfigEndpoints = ['/learn-data/learning-config.json', '/api/learning-config'] as const;
const configCache = new Map<string, LearningConfig>();

const fetchLearningConfigFromEndpoint = async (endpoint: string): Promise<LearningConfig | null> => {
  if (configCache.has(endpoint)) {
    return configCache.get(endpoint)!;
  }
  try {
    const res = await fetch(endpoint, { cache: 'no-store' });
    if (!res.ok) {
      return null;
    }
    const data = await res.json() as LearningConfig;
    const normalized: LearningConfig = {
      subjects: Array.isArray(data.subjects) ? data.subjects : [],
      pathMap: data.pathMap || {},
      labelMap: data.labelMap || {},
    };
    configCache.set(endpoint, normalized);
    return normalized;
  } catch (error) {
    console.warn('[learningStore] 加载配置失败', { endpoint, error });
    return null;
  }
};

const getLearningConfig = async (): Promise<LearningConfig> => {
  for (const endpoint of learningConfigEndpoints) {
    const cfg = await fetchLearningConfigFromEndpoint(endpoint);
    if (cfg && (cfg.subjects.length > 0 || (cfg.pathMap && Object.keys(cfg.pathMap).length > 0))) {
      return cfg;
    }
  }
  throw new Error('无法加载学习路径配置');
};

const parseMarkdownLearningPath = (markdown: string, subject: string): LearningPath => {
  const lines = markdown.split('\n');
  const path: LearningPath = { id: '', title: '', subject, chapters: [] };
  let currentChapter: Chapter | null = null;
  let currentGroup: { id: string; title: string; sections: Section[] } | null = null;
  const idRegex = /\(id: (.*?)\)/;

  const pathLine = lines.find((line) => line.startsWith('# '));
  if (pathLine) {
    path.title = pathLine.replace('# ', '').replace(idRegex, '').trim();
    const pathIdMatch = pathLine.match(idRegex);
    if (pathIdMatch) path.id = pathIdMatch[1];
  }

  for (const raw of lines) {
    const line = raw.trim();
    if (line.startsWith('## ')) {
      const rawTitle = line.replace('## ', '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      const idMatch = line.match(idRegex);
      if (idMatch) {
        currentChapter = { id: idMatch[1], title, groups: [], sections: [] };
        path.chapters.push(currentChapter);
        currentGroup = null;
      }
    } else if (line.startsWith('### ') && currentChapter) {
      const rawTitle = line.replace('### ', '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      const idMatch = line.match(idRegex);
      if (idMatch) {
        const group = { id: idMatch[1], title, sections: [] as Section[] };
        if (!currentChapter.groups) currentChapter.groups = [];
        currentChapter.groups.push(group);
        currentGroup = group;
      }
    } else if (line.startsWith('#### ') && currentChapter) {
      const rawTitle = line.replace('#### ', '').replace(idRegex, '').trim();
      const title = cleanTitle(rawTitle);
      const idMatch = line.match(idRegex);
      if (idMatch) {
        const section = {
          id: idMatch[1],
          title,
          chapterId: currentChapter.id,
        };
        if (currentGroup) {
          currentGroup.sections.push(section);
        } else {
          if (!currentChapter.sections) currentChapter.sections = [];
          currentChapter.sections.push(section);
        }
      }
    }
  }
  path.chapters = path.chapters.map((chapter, index) => {
    let groups = chapter.groups ? [...chapter.groups] : [];
    let sections = chapter.sections ? [...chapter.sections] : [];

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
  return path;
};

// Mock API functions - replace with real API calls
const mockLearningApi = {
  getLearningPath: async (subject: string): Promise<LearningPath> => {
    const config = await getLearningConfig();
    const available = config.subjects || [];
    let targetLang = subject;
    if (available.length > 0 && !available.includes(subject)) {
      targetLang = available[0];
    }

    let resourcePath = config.pathMap?.[targetLang] || null;
    if (!resourcePath) {
      const apiCfg = await fetchLearningConfigFromEndpoint('/api/learning-config');
      if (apiCfg?.pathMap?.[targetLang]) {
        resourcePath = apiCfg.pathMap[targetLang] ?? null;
      }
    }

    if (!resourcePath) {
      throw new Error(`No learning path found for subject: ${targetLang}`);
    }

    if (resourcePath.endsWith('.json')) {
      const res = await fetch(resourcePath, { cache: 'no-store' });
      if (!res.ok) {
        throw new Error(`Failed to fetch ${resourcePath}`);
      }
      const json = await res.json() as LearningPath;
      return {
        ...json,
        subject: json.subject || targetLang,
      };
    }

    const response = await fetch(resourcePath);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${resourcePath}`);
    }
    const markdown = await response.text();
    return parseMarkdownLearningPath(markdown, targetLang);
  },

  getSectionContent: async (sectionId: string, currentSubject?: string): Promise<SectionContent> => {
    try {
      // Resolve the concrete markdown file by id-prefix within the selected language folder
      const pref = typeof window !== 'undefined' ? (localStorage.getItem('preferred-subject') || localStorage.getItem('preferred-language')) : null;
      const lang = currentSubject || (pref || 'python');

      const resolveRes = await fetch(`/api/resolve-section?subject=${encodeURIComponent(lang)}&id=${encodeURIComponent(sectionId)}`);
      if (!resolveRes.ok) {
        throw new Error(`Markdown file not found for section: ${sectionId}`);
      }
      const { path: resolvedPath } = await resolveRes.json() as { path: string };
      const response = await fetch(resolvedPath);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${resolvedPath}`);
      }
      let markdown = await response.text();

      // 预处理：去除生成器前言与不必要的元数据注释
      try {
        // 去掉以 metadata 开头的 HTML 注释块
        markdown = markdown.replace(/<!--\s*metadata:[\s\S]*?-->/gi, '');

        // 安全定位到正文起始：找到首个不在代码块内的标题行（支持 # ~ ######）
        // 之前用的正则会误匹配代码块中的 "# ..." 注释，导致把前面的内容裁掉并破坏代码围栏
        const lines = markdown.split('\n');
        let inFence = false;
        let fenceChar: '`' | '~' | null = null;
        let firstHeadingLine = -1;

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];

          // 处理围栏代码块开始/结束（``` 或 ~~~）
          const fenceMatch = line.match(/^([`~]{3,})(.*)$/);
          if (fenceMatch) {
            const char = fenceMatch[1][0] as '`' | '~';
            if (!inFence) {
              inFence = true;
              fenceChar = char;
            } else if (char === fenceChar) {
              inFence = false;
              fenceChar = null;
            }
            continue;
          }

          // 仅在非代码块内识别 Markdown 标题
          if (!inFence && /^#{1,6}\s/.test(line)) {
            firstHeadingLine = i;
            break;
          }
        }

        if (firstHeadingLine > 0) {
          markdown = lines.slice(firstHeadingLine).join('\n');
        }

        // 清理开头多余空行
        markdown = markdown.replace(/^(\s*\n)+/, '');
      } catch {}

      const contentBlocks: (import('@/types').MarkdownBlock | import('@/types').InteractiveCodeBlock)[] = [];
      
      // Regex to split by interactive code blocks, keeping the delimiter in a capturing group
      const parts = markdown.split(/(\`\`\`(?:javascript|python|html):interactive[\s\S]*?\`\`\`)/g);

      for (const part of parts) {
        if (!part || part.trim() === '') continue;

        const interactiveMatch = part.match(/\`\`\`(javascript|python|html):interactive\n([\s\S]*?)\`\`\`/);

        if (interactiveMatch) {
          const codeLanguage = interactiveMatch[1];
          // Treat html as a static markdown block for display, not interactive execution
          if (codeLanguage === 'html') {
             const lastBlock = contentBlocks[contentBlocks.length - 1];
             if (lastBlock && lastBlock.type === 'markdown') {
                lastBlock.content += `\n\n\`\`\`html\n${interactiveMatch[2].trim()}\n\`\`\``;
            } else {
                contentBlocks.push({
                    type: 'markdown',
                    content: `\`\`\`html\n${interactiveMatch[2].trim()}\n\`\`\``,
                });
            }
          } else {
            contentBlocks.push({
                type: 'code',
                language: codeLanguage as 'javascript' | 'python',
                code: interactiveMatch[2].trim(),
                isInteractive: true,
            });
          }
        } else {
          // It's a markdown block
          const lastBlock = contentBlocks[contentBlocks.length - 1];
          if (lastBlock && lastBlock.type === 'markdown') {
            lastBlock.content += part;
          } else {
            contentBlocks.push({
              type: 'markdown',
              content: part,
            });
          }
        }
      }

      return { id: sectionId, contentBlocks };

    } catch (error) {
      console.warn(error);
      
      // Fallback content
      return {
        id: sectionId,
        contentBlocks: [
          {
            type: 'markdown',
            content: `# ${sectionId.split('-').pop()?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}\n\n此章节的内容正在精心准备中，敬请期待！`
          }
        ]
      };
    }
  }
};

const createWelcomeMessage = (userName?: string): ChatMessage => ({
  id: Date.now().toString(),
  sender: 'ai',
  content: userName 
    ? `Hi, ${userName}! 欢迎问我任何问题！选中内容可以直接引用哦`
    : `Hi！欢迎问我任何问题！选中内容可以直接引用哦`,
  timestamp: Date.now(),
});

export const useLearningStore = create<LearningState & LearningActions>()(
  persist(
    (set, get) => ({
      // State
      currentPath: null,
      currentSection: null,
      loadedPaths: {}, // 初始化为空对象
      loadedSections: {}, // 节内容缓存
      availableSubjects: undefined,
      subjectPathMap: undefined,
      subjectLabels: undefined,
      loading: {
        path: false,
        section: false,
        allPaths: false,
      },
      loadingPathSubject: null,
      pendingPathRequestId: null,
      pendingSectionRequestId: null,
      allPathsPrefetchScheduled: false,
      error: {
        path: null,
        section: null,
      },
      userCodeSnippets: {},
      uiState: {
        expandedChapters: [],
        searchQuery: '',
        navCollapsed: false,
        aiCollapsed: false,
        panelSizes: [15, 55, 30],
      },
      chatSessions: [],
      activeChatSessionId: null,
      aiProvider: 'deepseek' as AIProviderType,
      sendingMessage: false,
      fontSize: 16,
      fontFamilyId: null as unknown as string | null,
      fontFamily: null as unknown as string | null,
      selectedContent: null,
      userName: undefined,
      userProgress: {},
      mermaidErrors: [],
      // hybridServiceInitialized removed

      // Actions
      getFirstSectionId: (subject?: string) => {
        const state = get();
        const path = subject
          ? state.loadedPaths[subject] || state.currentPath
          : state.currentPath;
          
        if (!path) return null;
        
        // 尝试从第一章获取第一个 section
        const firstChapter = path.chapters[0];
        if (!firstChapter) return null;
        
        // 优先从 sections 获取
        if (firstChapter.sections && firstChapter.sections.length > 0) {
          return firstChapter.sections[0].id;
        }
        
        // 从 groups 获取
        if (firstChapter.groups && firstChapter.groups.length > 0) {
          const firstGroup = firstChapter.groups[0];
          if (firstGroup.sections && firstGroup.sections.length > 0) {
            return firstGroup.sections[0].id;
          }
        }
        
        return null;
      },
      
      discoverSubjects: async () => {
        try {
          const cfg = await getLearningConfig();
          set({
            availableSubjects: cfg.subjects,
            subjectPathMap: cfg.pathMap,
            subjectLabels: cfg.labelMap || {},
          });
        } catch (e) {
          // If discovery fails, leave state undefined and let downstream handlers fallback
          console.warn('discoverSubjects failed', e);
        }
      },
      initializeAllPaths: async () => {
        const state = get();
        if (state.loading.allPaths || state.allPathsPrefetchScheduled) return;

        set({ allPathsPrefetchScheduled: true });

        const runPrefetch = async () => {
          set(current => ({
            loading: { ...current.loading, allPaths: true },
            error: { ...current.error, path: null }
          }));

          try {
            if (!get().availableSubjects) {
              await get().discoverSubjects();
            }
            const snapshot = get();
            const langs = snapshot.availableSubjects && snapshot.availableSubjects.length > 0
              ? snapshot.availableSubjects
              : (['python','javascript','astrology','langgraph'] as string[]);
            const currentSubject = snapshot.currentPath?.subject || snapshot.preferredSubject || null;
            const loadedPathsSnapshot = snapshot.loadedPaths || {};

            const subjectsToPrefetch = langs.filter(lang =>
              lang !== currentSubject && !loadedPathsSnapshot[lang]
            );

            if (subjectsToPrefetch.length === 0) {
              set(current => ({
                loading: { ...current.loading, allPaths: false },
                allPathsPrefetchScheduled: false,
              }));
              return;
            }

            for (const subject of subjectsToPrefetch) {
              try {
                if (get().loadedPaths[subject]) {
                  continue;
                }
                const path = await mockLearningApi.getLearningPath(subject);
                set(prev => ({
                  loadedPaths: {
                    ...prev.loadedPaths,
                    [subject]: path,
                  },
                }));
                await new Promise(resolve => setTimeout(resolve, 160));
              } catch (prefetchError) {
                console.warn('[initializeAllPaths] 预取失败', { subject, prefetchError });
              }
            }

            const knowledgeLinkService = getKnowledgeLinkService();
            await knowledgeLinkService.initialize(get().loadedPaths);
            
            if (get().chatSessions.length === 0) {
              get().createNewChat();
            }

            set(current => ({
              loading: { ...current.loading, allPaths: false },
              error: { ...current.error, path: null },
              allPathsPrefetchScheduled: false,
            }));
          } catch (error) {
            set(current => ({
              loading: { ...current.loading, allPaths: false },
              error: { ...current.error, path: error instanceof Error ? error.message : 'Failed to initialize paths' },
              allPathsPrefetchScheduled: false,
            }));
          }
        };

        setTimeout(() => {
          runPrefetch().catch(err => {
            console.warn('[initializeAllPaths] 后台预取失败', err);
            set(current => ({
              loading: { ...current.loading, allPaths: false },
              allPathsPrefetchScheduled: false,
            }));
          });
        }, 400);
      },
      
      loadPath: async (subject: string) => {
        const state = get();
        
        console.log('%c[Store.loadPath] 📞 被调用', 'color: green; font-weight: bold', {
          requestedSubject: subject,
          currentSubject: state.currentPath?.subject,
          isLoading: state.loading.path,
          loadingSubject: state.loadingPathSubject,
          timestamp: new Date().toISOString()
        });
        
        if (state.currentPath?.subject === subject) {
          console.log('%c[Store.loadPath] ⏭️ 跳过 - 已加载或正在加载', 'color: gray', { subject });
          return;
        }

        const requestId = `${subject}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        
        set(state => ({
          loading: { ...state.loading, path: true },
          loadingPathSubject: subject,
          pendingPathRequestId: requestId,
          error: { ...state.error, path: null }
        }));

        try {
          // Ensure discovery so we can validate requested subject
          if (!get().availableSubjects) {
            await get().discoverSubjects();
          }
          const available = get().availableSubjects;
          let targetLang = subject;
          if (available && available.length > 0 && !available.includes(subject)) {
            // Fallback to the first available if requested one is not present
            targetLang = available[0];
          }

          const cachedPath = get().loadedPaths[targetLang];
          if (cachedPath) {
            if (get().pendingPathRequestId !== requestId) {
              console.log('%c[Store.loadPath] 🔄 忽略过期缓存结果', 'color: gray', {
                subject: targetLang,
                requestId,
              });
              return;
            }

            const snapshotBeforeSet = get();

            console.log('%c[Store.loadPath] ⚡ 命中缓存', 'color: green', {
              subject: targetLang,
              chaptersCount: cachedPath.chapters.length,
              timestamp: new Date().toISOString()
            });

            set({
              currentPath: cachedPath,
              loading: { ...snapshotBeforeSet.loading, path: false },
              loadingPathSubject: null,
              pendingPathRequestId: null,
              error: { ...snapshotBeforeSet.error, path: null },
              preferredSubject: targetLang,
            });

            try {
              localStorage.setItem('preferred-subject', targetLang);
              localStorage.setItem('preferred-language', targetLang);
            } catch {}

            if (get().chatSessions.length === 0) {
              get().createNewChat();
            }

            return;
          }

          const path = await mockLearningApi.getLearningPath(targetLang);

          if (get().pendingPathRequestId !== requestId) {
            console.log('%c[Store.loadPath] 🔄 忽略过期结果', 'color: gray', {
              subject: targetLang,
              requestId,
            });
            return;
          }

          const snapshotBeforeSet = get();
          
          // Update loadedPaths with the new path
          const updatedLoadedPaths = {
            ...snapshotBeforeSet.loadedPaths,
            [targetLang]: path
          };
          
          console.log('%c[Store.loadPath] ✅ 成功加载 Path', 'color: green; font-weight: bold', {
            subject: targetLang,
            pathId: path.id,
            chaptersCount: path.chapters.length,
            timestamp: new Date().toISOString()
          });
          
          set({
            currentPath: path,
            loadedPaths: updatedLoadedPaths,
            loading: { ...snapshotBeforeSet.loading, path: false },
            loadingPathSubject: null,
            pendingPathRequestId: null,
            error: { ...snapshotBeforeSet.error, path: null },
            preferredSubject: targetLang,
          });

          // Persist preferred subject for reloads (write both new and legacy keys for compatibility)
          try {
            localStorage.setItem('preferred-subject', targetLang);
            localStorage.setItem('preferred-language', targetLang);
          } catch {}
          
          // Initialize knowledge link service with all loaded paths
          const knowledgeLinkService = getKnowledgeLinkService();
          await knowledgeLinkService.initialize(updatedLoadedPaths);
          
          // If no chats exist, create a default one
          if (get().chatSessions.length === 0) {
            get().createNewChat();
          }

        } catch (error) {
          if (get().pendingPathRequestId !== requestId) {
            return;
          }
          const snapshotOnError = get();
          set({
            loading: { ...snapshotOnError.loading, path: false },
            loadingPathSubject: null,
            pendingPathRequestId: null,
            error: { ...snapshotOnError.error, path: error instanceof Error ? error.message : 'Failed to load learning path' }
          });
        }
      },

      loadSection: async (sectionId: string) => {
        const state = get();
        
        console.log('%c[Store.loadSection] 📞 被调用', 'color: teal; font-weight: bold', {
          requestedSection: sectionId,
          currentSection: state.currentSection?.id,
          currentPathSubject: state.currentPath?.subject,
          isLoading: state.loading.section,
          timestamp: new Date().toISOString()
        });
        
        if (state.currentSection?.id === sectionId) {
          console.log('%c[Store.loadSection] ⏭️ 跳过 - 已加载', 'color: gray', { sectionId });
          return;
        }

        const getCacheKey = (subject?: string | null, id: string = sectionId) =>
          subject ? `${subject}::${id}` : id;
        const candidateSubject = state.currentPath?.subject || state.loadingPathSubject || state.preferredSubject || null;
        let cacheKey = getCacheKey(candidateSubject);
        const cachedSection = state.loadedSections?.[cacheKey];

        const maybePrefetchNeighbors = (subject?: string | null) => {
          if (!subject) return;
          setTimeout(() => {
            const snapshot = get();
            const pathSnapshot = snapshot.currentPath;
            if (!pathSnapshot || pathSnapshot.subject !== subject) return;
            const sectionsFlat = pathSnapshot.chapters.flatMap(ch =>
              (ch.sections && ch.sections.length > 0)
                ? ch.sections
                : (ch.groups || []).flatMap(g => g.sections)
            );
            const currentIndex = sectionsFlat.findIndex(s => s.id === sectionId);
            if (currentIndex === -1) return;
            const neighborIds = [
              sectionsFlat[currentIndex + 1]?.id,
              sectionsFlat[currentIndex - 1]?.id,
            ].filter((id): id is string => Boolean(id));

            neighborIds.forEach((neighborId) => {
              const neighborKey = getCacheKey(subject, neighborId);
              const latest = get();
              if (latest.loadedSections[neighborKey]) return;
              mockLearningApi.getSectionContent(neighborId, subject)
                .then((content) => {
                  const afterFetch = get();
                  if (afterFetch.currentPath?.subject !== subject) return;
                  if (afterFetch.loadedSections[neighborKey]) return;
                  set(prev => ({
                    loadedSections: {
                      ...prev.loadedSections,
                      [neighborKey]: content,
                    },
                  }));
                })
                .catch((prefetchError) => {
                  console.debug('%c[Store.loadSection] 预取失败', 'color: gray', { neighborId, prefetchError });
                });
            });
          }, 50);
        };
        
        // ⚠️ 验证 section 是否属于当前 path
        if (state.currentPath) {
          const allSections = state.currentPath.chapters.flatMap(ch =>
            (ch.sections || []).concat((ch.groups || []).flatMap(g => g.sections || []))
          );
          const sectionExists = allSections.some(s => s.id === sectionId);
          if (!sectionExists) {
            console.warn('%c[Store.loadSection] ⚠️ 状态不匹配', 'color: red; font-weight: bold', {
              sectionId,
              currentPathSubject: state.currentPath.subject,
              message: `Section "${sectionId}" 不属于当前 Path "${state.currentPath.subject}"`
            });
          }
        }

        if (cachedSection) {
          console.log('%c[Store.loadSection] ⚡ 命中缓存', 'color: teal', { sectionId, cacheKey });
          set({
            currentSection: cachedSection,
            loading: { ...state.loading, section: false },
            pendingSectionRequestId: null,
            error: { ...state.error, section: null },
            lastOpenedSectionId: sectionId,
          });

          try {
            localStorage.setItem('last-opened-section', sectionId);
            const subjectToPersist = get().currentPath?.subject || candidateSubject;
            if (subjectToPersist) {
              localStorage.setItem('preferred-subject', subjectToPersist);
              localStorage.setItem('preferred-language', subjectToPersist);
            }
          } catch {}

          maybePrefetchNeighbors(get().currentPath?.subject || candidateSubject);
          return;
        }

        const requestId = `${sectionId}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        
        set(current => ({
          loading: { ...current.loading, section: true },
          pendingSectionRequestId: requestId,
          error: { ...current.error, section: null }
        }));

        try {
          const fallbackSubject = get().currentPath?.subject || candidateSubject;
          console.log('%c[Store.loadSection] 🔍 获取 Section 内容', 'color: teal', {
            sectionId,
            fallbackSubject
          });
          const content = await mockLearningApi.getSectionContent(sectionId, fallbackSubject || undefined);
          console.log('%c[Store.loadSection] ✅ 成功加载 Section', 'color: teal; font-weight: bold', {
            sectionId,
            blocksCount: content.contentBlocks.length,
            timestamp: new Date().toISOString()
          });

          if (get().pendingSectionRequestId !== requestId) {
            console.log('%c[Store.loadSection] 🔄 忽略过期结果', 'color: gray', { sectionId, requestId });
            return;
          }

          const snapshotBeforeSet = get();
          const resolvedSubject = snapshotBeforeSet.currentPath?.subject || fallbackSubject || candidateSubject;
          cacheKey = getCacheKey(resolvedSubject);
          
          set({
            currentSection: content,
            loading: { ...snapshotBeforeSet.loading, section: false },
            pendingSectionRequestId: null,
            error: { ...snapshotBeforeSet.error, section: null },
            lastOpenedSectionId: sectionId,
            loadedSections: {
              ...snapshotBeforeSet.loadedSections,
              [cacheKey]: content,
            },
          });

          // Persist last opened section and current subject for reloads
          try {
            localStorage.setItem('last-opened-section', sectionId);
            if (resolvedSubject) {
              localStorage.setItem('preferred-subject', resolvedSubject);
              localStorage.setItem('preferred-language', resolvedSubject);
            }
          } catch {}

          maybePrefetchNeighbors(resolvedSubject);
        } catch (error) {
          if (get().pendingSectionRequestId !== requestId) {
            return;
          }
          const snapshotOnError = get();
          set({
            loading: { ...snapshotOnError.loading, section: false },
            pendingSectionRequestId: null,
            error: { ...snapshotOnError.error, section: error instanceof Error ? error.message : 'Failed to load section content' }
          });
        }
      },

      updateUserCode: (sectionId: string, code: string) => {
        set(state => ({
          userCodeSnippets: {
            ...state.userCodeSnippets,
            [sectionId]: code
          }
        }));
      },

      updateUIState: (uiState: Partial<{ expandedChapters: string[]; searchQuery: string; navCollapsed: boolean; aiCollapsed: boolean; panelSizes: number[] }>) => {
        set((state) => ({
          uiState: {
            ...state.uiState,
            ...uiState
          }
        }));
      },

      // --- Chat Actions ---
      createNewChat: () => {
        const state = get();
        const newSession: ChatSession = {
          id: `chat-${Date.now()}`,
          title: '新的对话',
          messages: [createWelcomeMessage(state.userName)],
          createdAt: Date.now(),
        };
        set(state => ({
          chatSessions: [...state.chatSessions, newSession],
          activeChatSessionId: newSession.id,
        }));
      },

      switchChat: (sessionId: string) => {
        if (get().chatSessions.some(s => s.id === sessionId)) {
          set({ activeChatSessionId: sessionId });
        }
      },

      deleteChat: (sessionId: string) => {
        set(state => {
          const remainingSessions = state.chatSessions.filter(s => s.id !== sessionId);
          let newActiveId = state.activeChatSessionId;

          if (newActiveId === sessionId) {
            newActiveId = remainingSessions.length > 0 ? remainingSessions[0].id : null;
          }
          
          return {
            chatSessions: remainingSessions,
            activeChatSessionId: newActiveId,
          };
        });
      },
      
      renameChat: (sessionId: string, newTitle: string) => {
        set(state => ({
          chatSessions: state.chatSessions.map(session => 
            session.id === sessionId ? { ...session, title: newTitle } : session
          ),
        }));
      },

      addMessageToActiveChat: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
        set(state => {
          const activeId = state.activeChatSessionId;
          if (!activeId) return {};

          const newMessage: ChatMessage = {
            ...message,
            id: `${message.sender}-${Date.now()}`,
            timestamp: Date.now(),
          };

          return {
            chatSessions: state.chatSessions.map(session => {
              if (session.id === activeId) {
                // If it's the first user message, update the chat title
                const isFirstUserMessage = session.messages.filter(m => m.sender === 'user').length === 0 && message.sender === 'user';
                return {
                  ...session,
                  title: isFirstUserMessage ? message.content.substring(0, 20) : session.title,
                  messages: [...session.messages, newMessage],
                };
              }
              return session;
            }),
          };
        });
      },

      updateMessageContent: (sessionId: string, messageId: string, content: string) => {
        set(state => ({
          chatSessions: state.chatSessions.map(session => {
            if (session.id === sessionId) {
              return {
                ...session,
                messages: session.messages.map(message =>
                  message.id === messageId ? { ...message, content } : message
                ),
              };
            }
            return session;
          }),
        }));
      },

      updateMessageLinks: (sessionId: string, messageId: string, linkedSections: SectionLink[]) => {
        set(state => ({
          chatSessions: state.chatSessions.map(session => {
            if (session.id === sessionId) {
              return {
                ...session,
                messages: session.messages.map(message =>
                  message.id === messageId ? { ...message, linkedSections } : message
                ),
              };
            }
            return session;
          }),
        }));
      },

      setFontSize: (fontSize: number) => {
        set({ fontSize });
      },

      // Font family selection
      setFontFamily: (id: string | null, family: string | null) => {
        set({ fontFamilyId: id, fontFamily: family || null });
        try {
          if (typeof window !== 'undefined') {
            if (family) {
              localStorage.setItem('preferred-font-family', family);
              localStorage.setItem('preferred-font-id', id || '');
            } else {
              localStorage.removeItem('preferred-font-family');
              localStorage.removeItem('preferred-font-id');
            }
          }
        } catch {}
      },

      // Context Selection Actions
      setSelectedContent: (content: ContextReference | null) => {
        set({ selectedContent: content });
      },

      // User Actions
      setUserName: (name: string) => {
        set({ userName: name });
      },

      // AI Provider Actions
      setAIProvider: (provider: AIProviderType) => {
        set({ aiProvider: provider });
      },

      // User Progress Actions
      toggleSectionComplete: (sectionId: string) => {
        set(state => {
          const progress = state.userProgress[sectionId] || {
            sectionId,
            isCompleted: false,
            isFavorite: false,
          };
          
          const updatedProgress = {
            ...progress,
            isCompleted: !progress.isCompleted,
            completedAt: !progress.isCompleted ? Date.now() : undefined,
          };
          
          return {
            userProgress: {
              ...state.userProgress,
              [sectionId]: updatedProgress,
            },
          };
        });
      },
      
      toggleSectionFavorite: (sectionId: string) => {
        set(state => {
          const progress = state.userProgress[sectionId] || {
            sectionId,
            isCompleted: false,
            isFavorite: false,
          };
          
          const updatedProgress = {
            ...progress,
            isFavorite: !progress.isFavorite,
            favoritedAt: !progress.isFavorite ? Date.now() : undefined,
          };
          
          return {
            userProgress: {
              ...state.userProgress,
              [sectionId]: updatedProgress,
            },
          };
        });
      },
      
      getSectionProgress: (sectionId: string) => {
        return get().userProgress[sectionId];
      },
      
      getCompletedCount: () => {
        const progress = get().userProgress;
        return Object.values(progress).filter(p => p.isCompleted).length;
      },
      
      getFavoriteCount: () => {
        const progress = get().userProgress;
        return Object.values(progress).filter(p => p.isFavorite).length;
      },

      // Mermaid diagnostics actions
      reportMermaidError: (entry) => {
        set((state) => ({ mermaidErrors: [...(state.mermaidErrors || []), entry] }));
        try { console.warn('[MermaidError]', entry); } catch {}
      },
      clearMermaidErrors: () => set({ mermaidErrors: [] }),

      // 初始化混合知识链接服务
      // initializeHybridService removed

      sendChatMessage: async (content: string, contextReference?: ContextReference | null) => {
        const state = get();
        const activeSessionId = state.activeChatSessionId;
        
        if (!activeSessionId || state.sendingMessage) {
          return;
        }

        // Add user message
        get().addMessageToActiveChat({
          content,
          sender: 'user',
          contextReference: contextReference || undefined,
        });

        // Add a placeholder for AI response
        const aiMessageId = `ai-${Date.now()}`;
        get().addMessageToActiveChat({
          id: aiMessageId,
          content: '▍', // Placeholder for streaming
          sender: 'ai',
        });

        set({ sendingMessage: true });

        try {
          const activeSession = get().chatSessions.find(s => s.id === activeSessionId);
          if (!activeSession) throw new Error('No active session');

          const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              messages: activeSession.messages.filter(m => m.id !== aiMessageId), // Exclude placeholder
              provider: state.aiProvider,
              contextReference: contextReference,
              language: state.currentPath?.subject,
            }),
          });

          if (!response.ok || !response.body) {
            throw new Error(`API error: ${response.status}`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let accumulatedContent = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const delta = decoder.decode(value);
            accumulatedContent += delta;
            get().updateMessageContent(activeSessionId, aiMessageId, accumulatedContent + '▍');
          }
          // Remove the typing cursor at the end
          get().updateMessageContent(activeSessionId, aiMessageId, accumulatedContent);
          
          // Chat-time knowledge matching via vectors removed

        } catch (error) {
          console.error('Chat error:', error);
          const errorMessage = '抱歉，发送消息时出现错误。请稍后重试。';
          get().updateMessageContent(activeSessionId, aiMessageId, errorMessage);
        } finally {
          set({ sendingMessage: false });
        }
      },
    }),
    {
      name: 'learning-store',
      partialize: (state: import('@/types').LearningState & import('@/types').LearningActions) => ({
        userCodeSnippets: state.userCodeSnippets,
        uiState: state.uiState,
        chatSessions: state.chatSessions,
        activeChatSessionId: state.activeChatSessionId,
        fontSize: state.fontSize,
        fontFamilyId: state.fontFamilyId,
        fontFamily: state.fontFamily,
        userName: state.userName,
        aiProvider: state.aiProvider,
        userProgress: state.userProgress,
        preferredSubject: state.preferredSubject,
        lastOpenedSectionId: state.lastOpenedSectionId,
      }),
      storage: createJSONStorage(() => {
        // Check if we're on the client side
        if (typeof window !== 'undefined') {
          return localStorage;
        }
        // Return a no-op storage for server side
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        };
      }),
      skipHydration: typeof window === 'undefined',
      version: 1,
      migrate: <T>(persistedState: T): T => {
        // Migration logic if needed in the future
        return persistedState;
      },
    }
  )
);

declare global {
  interface Window {
    __learningStore?: typeof useLearningStore;
  }
}

// Initial state for non-persisted parts
// if (typeof window !== 'undefined') {
//   useLearningStore.setState({
//     currentPath: null,
//     currentSection: null,
//     loading: { path: false, section: false },
//     error: { path: null, section: null },
//     selectedContent: null,
//     sendingMessage: false,
//     preferredSubject: undefined,
//     lastOpenedSectionId: null,
//     mermaidErrors: [],
//   });
// }

// Expose store for debugging in browser console
try {
  if (typeof window !== 'undefined') {
    window.__learningStore = useLearningStore;
  }
} catch {}

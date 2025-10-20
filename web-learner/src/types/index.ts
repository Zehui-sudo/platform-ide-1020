// 一级目录: 学习路径 (代表一门课程)
export interface LearningPath {
  id: string; // e.g., "python-basics"
  title: string; // e.g., "Python 核心基础"
  subject: string; // dynamic subject code discovered from /public/content
  chapters: Chapter[];
}

// 二级目录: 章 (代表一个知识模块)
export interface Chapter {
  id: string; // e.g., "py-ch-2-control-flow"
  title: string; // e.g., "控制流程"
  // 正式三级结构：优先使用 groups；为兼容旧数据，sections 可选
  groups?: SectionGroup[];
  sections?: Section[];
}

// 新增：小类分组（第三级之前的分组，如 1.1 变量与值）
export interface SectionGroup {
  id: string;    // e.g., "js-gr-1-1"
  title: string; // e.g., "1.1 变量与值"
  sections: Section[];
}

// 三级目录: 节 (代表一个具体知识点)
export interface Section {
  id: string; // e.g., "py-sec-2-1-if-statement"
  title: string; // e.g., "if 条件语句"
  chapterId: string; // 父章节的ID
}

// 节内容 (由内容块数组组成)
export interface SectionContent {
  id: string; // 与 Section.id 对应
  contentBlocks: (MarkdownBlock | InteractiveCodeBlock)[];
}

// 内容块1: Markdown 静态内容
export interface MarkdownBlock {
  type: 'markdown';
  content: string;
}

// 内容块2: 交互式代码
export interface InteractiveCodeBlock {
  type: 'code';
  language: 'python' | 'javascript';
  code: string;
  isInteractive: true;
}

// 用户进度数据
export interface UserProgress {
  sectionId: string;
  isCompleted: boolean;
  isFavorite: boolean;
  completedAt?: number;
  favoritedAt?: number;
}

// UI状态类型
export interface UIState {
  expandedChapters: string[];
  searchQuery: string;
  navCollapsed?: boolean;
  aiCollapsed?: boolean;
}

// 知识点链接
export interface SectionLink {
  sectionId: string;          // 章节 ID
  title: string;              // 章节标题
  chapterId: string;          // 所属章节 ID
  chapterTitle?: string;      // 章节标题
  subject: string; // dynamic subject
  matchedKeywords?: string[]; // 匹配到的关键词
  relevanceScore?: number;    // 相关性分数 (0-1)
  // 混合匹配新增字段
  fusedScore?: number;        // 融合后的最终分数
  matchType?: 'keyword' | 'semantic' | 'hybrid';  // 匹配类型
  confidence?: 'high' | 'medium' | 'low';         // 置信度
  explanation?: string;       // 匹配理由说明
  sourceMatches?: string[];   // 来源匹配（keyword/semantic）
}

// 知识点索引条目
export interface KnowledgeIndexEntry {
  sectionId: string;
  title: string;
  chapterId: string;
  chapterTitle: string;
  subject: string; // dynamic subject
  keywords: string[];           // 主要关键词
  aliases: string[];            // 同义词和别名
  concepts: string[];           // 相关概念
  contentPreview?: string;      // 内容预览（前100字）
  codeExamples?: string[];      // 代码示例中的关键函数/类名
}

// Pyodide状态类型
export type PyodideStatus = 'unloaded' | 'loading' | 'ready' | 'error';

// 全局状态类型
export interface LearningState {
  currentPath: LearningPath | null;
  currentSection: SectionContent | null;
  loadedPaths: Record<string, LearningPath>; // 存储所有已加载的路径（动态语言）
  // Auto-discovery of available languages and their learning-path locations
  availableSubjects?: string[];
  subjectPathMap?: Partial<Record<string, string | null>>;
  subjectIcons?: Record<string, string>; // 存储学科对应的图标路径
  subjectLabels?: Record<string, string>; // 学习路径的人类可读名称（来自 learning-path H1）
  loading: {
    path: boolean;
    section: boolean;
  };
  error: {
    path: string | null;
    section: string | null;
  };
  userCodeSnippets: Record<string, string>; // Key: SectionID, Value: User's code
  uiState: UIState;
  userProgress: Record<string, UserProgress>; // Key: sectionId
  // AI Chat State
  chatSessions: ChatSession[];
  activeChatSessionId: string | null;
  // AI Provider State
  aiProvider: AIProviderType;
  sendingMessage: boolean;
  // Pyodide State
  pyodideStatus: PyodideStatus;
  pyodideError: string | null;
  // Font Size State
  fontSize: number;
  // Font family selection (global, excludes code blocks)
  fontFamilyId?: string | null;
  fontFamily?: string | null;
  // Context Selection State
  selectedContent: ContextReference | null;
  // User Info
  userName?: string;
  // Preferred language & last opened section
  preferredSubject?: string;
  lastOpenedSectionId?: string | null;
  // Hybrid Knowledge Link Service State
  // hybridServiceInitialized removed
  // Mermaid runtime parse errors (non-persisted)
  mermaidErrors?: MermaidErrorEntry[];
}

// AI 对话消息
export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: number; // 使用时间戳以方便序列化
  contextReference?: ContextReference; // 引用的上下文内容
  linkedSections?: SectionLink[]; // 相关知识点链接
}

// 上下文引用
export interface ContextReference {
  text: string; // 引用的文本内容
  source?: string; // 来源（如章节标题）
  type?: 'markdown' | 'code'; // 内容类型
  // 进阶上下文（可选）
  blockIndex?: number;          // 所在代码块在全文中的序号（从0开始）
  progressPercent?: number;     // 估算已阅读进度 0-100
  readSoFar?: string;           // 从文首到当前块（含当前块）的已读内容节选（Markdown+代码）
  sectionId?: string;           // 当前代码块对应的交互块ID（用于取用户最新代码）
}

// AI 对话会话
export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
}

export interface LearningActions {
  loadPath: (subject: string) => Promise<void>;
  discoverSubjects: () => Promise<void>; // 自动发现可用学科与学习路径
  initializeAllPaths: () => Promise<void>; // 初始化所有学科的学习路径
  loadSection: (sectionId: string) => Promise<void>;
  updateUserCode: (sectionId: string, code: string) => void;
  updateUIState: (uiState: Partial<UIState>) => void;
  // AI Chat Actions
  createNewChat: () => void;
  switchChat: (sessionId: string) => void;
  deleteChat: (sessionId: string) => void;
  renameChat: (sessionId: string, newTitle: string) => void;
  addMessageToActiveChat: (message: Partial<ChatMessage> & { sender: 'user' | 'ai', content: string }) => void;
  updateMessageContent: (sessionId: string, messageId: string, content: string) => void;
  updateMessageLinks: (sessionId: string, messageId: string, linkedSections: SectionLink[]) => void;
  // AI Provider Actions
  setAIProvider: (provider: AIProviderType) => void;
  sendChatMessage: (content: string, contextReference?: ContextReference | null, language?: string) => Promise<void>;
  // Pyodide Actions
  loadPyodide: () => Promise<void>;
  // Font Size Actions
  setFontSize: (fontSize: number) => void;
  // Font Family Actions
  setFontFamily: (id: string | null, family: string | null) => void;
  // Context Selection Actions
  setSelectedContent: (content: ContextReference | null) => void;
  // User Actions
  setUserName: (name: string) => void;
  // User Progress Actions
  toggleSectionComplete: (sectionId: string) => void;
  toggleSectionFavorite: (sectionId: string) => void;
  getSectionProgress: (sectionId: string) => UserProgress | undefined;
  getCompletedCount: () => number;
  getFavoriteCount: () => number;
  // (hybrid knowledge link removed)
  // Mermaid error reporting
  reportMermaidError: (entry: MermaidErrorEntry) => void;
  clearMermaidErrors: () => void;
}

// API 响应类型
export interface LearningApi {
  getLearningPath: (subject: string) => Promise<LearningPath>;
  getSectionContent: (sectionId: string) => Promise<SectionContent>;
}

// AI Provider Types
export type AIProviderType = 'openai' | 'anthropic' | 'deepseek' | 'doubao';

// AI Chat API Types
export interface ChatAPIRequest {
  messages: ChatMessage[];
  provider: AIProviderType;
  model?: string;
  contextReference?: ContextReference;
  language?: string;
}

export interface ChatAPIResponse {
  content: string;
  provider: AIProviderType;
  model: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  error?: string;
}

// Mermaid diagnostics
export interface MermaidErrorEntry {
  sectionId?: string;
  markdownIndex?: number;
  error: string;
  code: string;
  normalizedCode?: string;
  recovered?: boolean; // true if fallback rendered
  timestamp: number;
}

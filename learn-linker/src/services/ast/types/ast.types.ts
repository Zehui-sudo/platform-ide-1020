/**
 * AST 特征提取相关类型定义
 */

/**
 * 原子特征 - AST 直接提取的基础特征
 */
export interface AtomicFeatures {
  /** 语法特征：变量声明、函数、类等 */
  syntax: string[];
  /** API 调用：Array.map、Promise.all 等 */
  api: string[];
  /** 操作类型：循环、条件、异常处理等 */
  operations: string[];
}

/**
 * 结构特征 - 从 AST 分析得出的模式
 */
export interface StructuralFeatures {
  /** 代码模式：async-await、promise-chain 等 */
  patterns: string[];
  /** 嵌套深度 */
  nesting: number;
  /** 圈复杂度 */
  complexity: number;
}

/**
 * 统计特征 - 用于推断用户水平
 */
export interface StatisticalFeatures {
  /** 按难度分类的语法分布 */
  syntaxDistribution: {
    basic: string[];
    intermediate: string[];
    advanced: string[];
  };
  /** 各难度级别的特征计数 */
  featureCount: {
    basicCount: number;
    intermediateCount: number;
    advancedCount: number;
  };
}

/**
 * 完整的 AST 特征集合
 */
export interface AstFeatures {
  atomic: AtomicFeatures;
  structural: StructuralFeatures;
  statistical: StatisticalFeatures;
}

/**
 * 知识点定义
 */
export interface KnowledgeDefinition {
  /** 知识点 ID，如 js-sec-5-3 */
  id: string;
  /** 知识点标题 */
  title: string;
  /** 必须包含的特征 */
  requiredFeatures: string[];
  /** 可选特征（加分项） */
  optionalFeatures: string[];
  /** 特征权重映射 */
  weight: Map<string, number>;
  /** 难度级别 */
  difficulty: 'basic' | 'intermediate' | 'advanced';
  /** 前置知识点 */
  dependencies?: string[];
  /** 知识类别 */
  category: string;
}

/**
 * 知识点匹配结果
 */
export interface KnowledgeMatchResult {
  /** 主要知识点 ID */
  primaryKnowledge: string | null;
  /** 所有匹配结果 */
  allMatches: Array<{
    id: string;
    score: number;
    knowledge: KnowledgeDefinition;
  }>;
  /** 推断的用户水平 */
  userLevel: 'beginner' | 'intermediate' | 'advanced';
  /** 知识覆盖度分布 */
  coverage: {
    basic: number;
    intermediate: number;
    advanced: number;
  };
}

/**
 * 统一输出格式
 */
export interface UnifiedOutput {
  /** 给 AI 的上下文信息 */
  aiContext: {
    code: string;
    extractedFeatures: AstFeatures;
    userLevel: string;
    primaryTopic: string | null;
    instruction: string;
  };
  /** 知识点链接列表 */
  knowledgeLinks: Array<{
    id: string;
    title: string;
    relevance: number;
  }>;
}

/**
 * 语言特定的特征映射
 */
export interface LanguageMapping {
  /** 语法节点类型到特征的映射 */
  syntaxMap: Record<string, string>;
  /** 模式组合到特征的映射 */
  patternMap: Record<string, string>;
}

/**
 * 支持的编程语言
 */
export type SupportedLanguage = 'javascript' | 'typescript' | 'tsx' | 'python' | 'java' | 'go' | 'rust';

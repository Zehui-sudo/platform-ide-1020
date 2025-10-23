import { TreeSitterParser } from './TreeSitterParser';
import { FeatureExtractor } from './FeatureExtractor';
import { KnowledgeMatcher } from './KnowledgeMatcher';
import { UnifiedOutput, AstFeatures, KnowledgeMatchResult } from './types/ast.types';

/**
 * 统一的 AST 分析器
 * 整合特征提取、知识匹配和输出生成
 */
export class UnifiedAstAnalyzer {
  private static instance: UnifiedAstAnalyzer | null = null;
  private parser: TreeSitterParser;
  private extractor: FeatureExtractor;
  private matcher: KnowledgeMatcher;
  private initialized = false;

  private constructor() {
    this.parser = new TreeSitterParser();
    this.extractor = new FeatureExtractor(this.parser);
    this.matcher = new KnowledgeMatcher();
  }

  /**
   * 获取单例实例
   */
  static getInstance(): UnifiedAstAnalyzer {
    if (!UnifiedAstAnalyzer.instance) {
      UnifiedAstAnalyzer.instance = new UnifiedAstAnalyzer();
    }
    return UnifiedAstAnalyzer.instance;
  }

  /**
   * 初始化分析器
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }
    
    try {
      await this.parser.initialize();
      this.initialized = true;
      console.log('Unified AST Analyzer initialized');
    } catch (error) {
      console.error('Failed to initialize analyzer:', error);
      // 降级处理：即使初始化失败也允许使用基础功能
      this.initialized = true;
    }
  }

  /**
   * 分析代码
   */
  async analyzeCode(code: string, language: string): Promise<UnifiedOutput> {
    // 确保初始化
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Step 1: 提取特征
      console.log('Extracting features from code...');
      const features = await this.extractor.extractFeatures(code, language);
      console.log('Features extracted:', {
        syntaxCount: features.atomic.syntax.length,
        apiCount: features.atomic.api.length,
        patterns: features.structural.patterns
      });

      // Step 2: 匹配知识点
      console.log('Matching knowledge points...');
      const matchResult = await this.matcher.matchKnowledge(features);
      console.log('Knowledge matched:', {
        primary: matchResult.primaryKnowledge,
        matchCount: matchResult.allMatches.length,
        userLevel: matchResult.userLevel
      });

      // Step 3: 生成统一输出
      return this.generateUnifiedOutput(code, features, matchResult);
    } catch (error) {
      console.error('Analysis failed:', error);
      // 返回默认输出
      return this.generateFallbackOutput(code);
    }
  }

  /**
   * 生成统一输出
   */
  private generateUnifiedOutput(
    code: string,
    features: AstFeatures,
    matchResult: KnowledgeMatchResult
  ): UnifiedOutput {
    const instruction = this.generateAiInstruction(
      matchResult.userLevel,
      matchResult.primaryKnowledge,
      features,
      matchResult
    );

    // 获取推荐的学习路径
    const learningPath = this.matcher.getRecommendedPath(
      matchResult.primaryKnowledge,
      matchResult.userLevel
    );

    return {
      aiContext: {
        code,
        extractedFeatures: features,
        userLevel: matchResult.userLevel,
        primaryTopic: matchResult.primaryKnowledge,
        instruction
      },
      knowledgeLinks: this.formatKnowledgeLinks(matchResult, learningPath)
    };
  }

  /**
   * 生成 AI 指导语
   */
  private generateAiInstruction(
    level: string,
    topic: string | null,
    features: AstFeatures,
    matchResult: KnowledgeMatchResult
  ): string {
    // 构建特征摘要
    const featureSummary = this.summarizeFeatures(features);
    
    // 根据用户水平生成不同的指导
    let instruction = '';
    
    if (!topic) {
      instruction = `请解释这段代码的功能。代码特征：${featureSummary}`;
    } else {
      const primaryMatch = matchResult.allMatches.find(m => m.id === topic);
      const topicTitle = primaryMatch?.knowledge.title || topic;
      
      switch (level) {
        case 'advanced':
          instruction = `这段代码涉及【${topicTitle}】相关的高级特性。
检测到的特征：${featureSummary}
假设用户已掌握基础知识（变量、函数、对象、数组等），请：
1. 重点解释 ${topicTitle} 的核心概念和工作原理
2. 分析代码中的具体实现方式
3. 提供最佳实践建议和潜在优化点
4. 不需要解释基础语法`;
          break;
          
        case 'intermediate':
          instruction = `这段代码涉及【${topicTitle}】。
检测到的特征：${featureSummary}
用户具备一定编程基础，请：
1. 简要回顾相关基础概念
2. 重点解释 ${topicTitle} 的使用方法
3. 分析代码逻辑和执行流程
4. 提供常见使用场景`;
          break;
          
        default: // beginner
          instruction = `这段代码涉及【${topicTitle}】。
检测到的特征：${featureSummary}
用户可能是初学者，请：
1. 从基础概念开始解释
2. 逐行分析代码的作用
3. 解释每个语法元素的含义
4. 使用简单易懂的语言和类比`;
      }
    }
    
    // 添加相关知识点提示
    if (matchResult.allMatches.length > 1) {
      const otherTopics = matchResult.allMatches
        .slice(1, 4) // 最多3个相关主题
        .map(m => m.knowledge.title)
        .join('、');
      instruction += `\n\n相关知识点：${otherTopics}`;
    }
    
    return instruction;
  }

  /**
   * 总结特征
   */
  private summarizeFeatures(features: AstFeatures): string {
    const summary: string[] = [];
    
    // 主要语法特征
    const mainSyntax = features.atomic.syntax.slice(0, 5).join('、');
    if (mainSyntax) {
      summary.push(`语法：${mainSyntax}`);
    }
    
    // 主要 API
    const mainApi = features.atomic.api.slice(0, 3).join('、');
    if (mainApi) {
      summary.push(`API：${mainApi}`);
    }
    
    // 代码模式
    if (features.structural.patterns.length > 0) {
      summary.push(`模式：${features.structural.patterns.join('、')}`);
    }
    
    // 复杂度
    if (features.structural.complexity > 5) {
      summary.push(`复杂度：高(${features.structural.complexity})`);
    }
    
    return summary.join('；') || '基础代码';
  }

  /**
   * 格式化知识点链接
   */
  private formatKnowledgeLinks(
    matchResult: KnowledgeMatchResult,
    learningPath: string[]
  ): Array<{ id: string; title: string; relevance: number }> {
    const links = [];
    const added = new Set<string>();
    
    // 首先添加主要知识点
    if (matchResult.primaryKnowledge) {
      const primary = matchResult.allMatches.find(m => m.id === matchResult.primaryKnowledge);
      if (primary) {
        links.push({
          id: primary.id,
          title: `📌 ${primary.knowledge.title}`,
          relevance: primary.score
        });
        added.add(primary.id);
      }
    }
    
    // 添加学习路径中的依赖知识点
    for (const pathId of learningPath) {
      if (!added.has(pathId)) {
        const match = matchResult.allMatches.find(m => m.id === pathId);
        if (match) {
          links.push({
            id: match.id,
            title: `📚 ${match.knowledge.title} (前置)`,
            relevance: match.score
          });
          added.add(match.id);
        }
      }
    }
    
    // 添加其他相关知识点
    for (const match of matchResult.allMatches) {
      if (!added.has(match.id) && links.length < 8) {
        links.push({
          id: match.id,
          title: match.knowledge.title,
          relevance: match.score
        });
        added.add(match.id);
      }
    }
    
    return links;
  }

  /**
   * 生成降级输出（当分析失败时）
   */
  private generateFallbackOutput(code: string): UnifiedOutput {
    return {
      aiContext: {
        code,
        extractedFeatures: {
          atomic: { syntax: [], api: [], operations: [] },
          structural: { patterns: [], nesting: 0, complexity: 1 },
          statistical: {
            syntaxDistribution: { basic: [], intermediate: [], advanced: [] },
            featureCount: { basicCount: 0, intermediateCount: 0, advancedCount: 0 }
          }
        },
        userLevel: 'intermediate',
        primaryTopic: null,
        instruction: '请解释这段代码的功能和实现原理。'
      },
      knowledgeLinks: []
    };
  }

  /**
   * 清理资源
   */
  dispose(): void {
    this.parser.dispose();
    UnifiedAstAnalyzer.instance = null;
  }
}

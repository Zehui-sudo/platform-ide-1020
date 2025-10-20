import { 
  AstFeatures, 
  KnowledgeDefinition, 
  KnowledgeMatchResult,
  StatisticalFeatures 
} from './types/ast.types';
import { knowledgeDefinitions } from './config/knowledgeBase';

/**
 * 知识点匹配器
 */
export class KnowledgeMatcher {
  private knowledgeBase: Map<string, KnowledgeDefinition>;

  constructor() {
    this.knowledgeBase = new Map();
    this.loadKnowledgeDefinitions();
  }

  /**
   * 加载知识点定义
   */
  private loadKnowledgeDefinitions(): void {
    for (const knowledge of knowledgeDefinitions) {
      this.knowledgeBase.set(knowledge.id, knowledge);
    }
    console.log(`Loaded ${this.knowledgeBase.size} knowledge definitions`);
  }

  /**
   * 匹配知识点
   */
  async matchKnowledge(features: AstFeatures): Promise<KnowledgeMatchResult> {
    const matches = [];

    // 遍历所有知识点，计算匹配分数
    for (const [id, knowledge] of this.knowledgeBase) {
      const score = this.calculateMatchScore(features, knowledge);
      
      if (score > 0.3) {  // 降低阈值，包含更多相关知识点
        matches.push({ id, score, knowledge });
      }
    }

    // 按分数排序
    matches.sort((a, b) => b.score - a.score);

    // 选择主要知识点
    const primaryKnowledge = matches[0]?.id || null;

    // 推断用户水平
    const userLevel = this.inferUserLevel(features.statistical);

    // 计算知识覆盖度
    const coverage = this.calculateCoverage(features.statistical);

    // 根据用户水平和依赖关系调整推荐
    const adjustedMatches = this.adjustMatchesForUserLevel(matches, userLevel);

    return {
      primaryKnowledge,
      allMatches: adjustedMatches,
      userLevel,
      coverage
    };
  }

  /**
   * 计算匹配分数
   */
  private calculateMatchScore(
    features: AstFeatures,
    knowledge: KnowledgeDefinition
  ): number {
    let score = 0;
    let requiredMatched = 0;
    const requiredTotal = knowledge.requiredFeatures.length;

    // 合并所有特征
    const allFeatures = [
      ...features.atomic.syntax,
      ...features.atomic.api,
      ...features.atomic.operations,
      ...features.structural.patterns
    ];

    // 检查必需特征
    for (const required of knowledge.requiredFeatures) {
      if (this.featureMatches(required, allFeatures)) {
        requiredMatched++;
        const weight = knowledge.weight.get(required) || 1.0;
        score += weight;
      }
    }

    // 如果必需特征匹配率太低，直接返回 0
    if (requiredTotal > 0 && requiredMatched / requiredTotal < 0.5) {
      return 0;
    }

    // 可选特征加分
    for (const optional of knowledge.optionalFeatures) {
      if (this.featureMatches(optional, allFeatures)) {
        const weight = knowledge.weight.get(optional) || 0.3;
        score += weight;
      }
    }

    // 根据复杂度调整分数
    score = this.adjustScoreByComplexity(score, features.structural.complexity, knowledge.difficulty);

    return score;
  }

  /**
   * 检查特征是否匹配（支持模糊匹配）
   */
  private featureMatches(required: string, features: string[]): boolean {
    // 精确匹配
    if (features.includes(required)) {
      return true;
    }

    // 模糊匹配规则
    const fuzzyRules: Record<string, string[]> = {
      'array-method': ['Array.map', 'Array.filter', 'Array.reduce', '.map', '.filter', '.reduce'],
      'promise': ['Promise', 'Promise.all', 'Promise.race', '.then', '.catch'],
      'async': ['async', 'async-await', 'async-function'],
      'loop': ['for-loop', 'while-loop', 'do-while', 'for-in', 'for-of'],
      'conditional': ['if-else', 'ternary', 'switch'],
      'function': ['function', 'arrow-function', 'async-function'],
      'variable-declaration': ['let', 'const', 'var']
    };

    // 检查模糊匹配
    const alternatives = fuzzyRules[required];
    if (alternatives) {
      return alternatives.some(alt => features.includes(alt));
    }

    // 部分匹配（如 Array.map 匹配 map）
    return features.some(f => f.includes(required) || required.includes(f));
  }

  /**
   * 根据代码复杂度调整分数
   */
  private adjustScoreByComplexity(
    score: number,
    complexity: number,
    knowledgeDifficulty: string
  ): number {
    // 复杂代码更可能涉及高级知识点
    if (knowledgeDifficulty === 'advanced' && complexity > 5) {
      return score * 1.2;
    }
    
    // 简单代码更可能是基础知识点
    if (knowledgeDifficulty === 'basic' && complexity <= 2) {
      return score * 1.1;
    }

    return score;
  }

  /**
   * 推断用户水平
   */
  private inferUserLevel(stats: StatisticalFeatures): 'beginner' | 'intermediate' | 'advanced' {
    const { featureCount } = stats;
    const total = featureCount.basicCount + 
                  featureCount.intermediateCount + 
                  featureCount.advancedCount;

    if (total === 0) return 'beginner';

    const advancedRatio = featureCount.advancedCount / total;
    const intermediateRatio = featureCount.intermediateCount / total;
    const basicRatio = featureCount.basicCount / total;

    // 根据特征分布判断水平
    if (advancedRatio > 0.4) {
      return 'advanced';
    } else if (intermediateRatio > 0.4 || (intermediateRatio > 0.3 && advancedRatio > 0.2)) {
      return 'intermediate';
    } else {
      return 'beginner';
    }
  }

  /**
   * 计算知识覆盖度
   */
  private calculateCoverage(stats: StatisticalFeatures): {
    basic: number;
    intermediate: number;
    advanced: number;
  } {
    const { featureCount } = stats;
    const total = featureCount.basicCount + 
                  featureCount.intermediateCount + 
                  featureCount.advancedCount;

    if (total === 0) {
      return { basic: 0, intermediate: 0, advanced: 0 };
    }

    return {
      basic: featureCount.basicCount / total,
      intermediate: featureCount.intermediateCount / total,
      advanced: featureCount.advancedCount / total
    };
  }

  /**
   * 根据用户水平调整匹配结果
   */
  private adjustMatchesForUserLevel(
    matches: Array<{ id: string; score: number; knowledge: KnowledgeDefinition }>,
    userLevel: 'beginner' | 'intermediate' | 'advanced'
  ): Array<{ id: string; score: number; knowledge: KnowledgeDefinition }> {
    const adjusted = [...matches];

    // 为初学者增加基础知识点的权重
    if (userLevel === 'beginner') {
      adjusted.forEach(match => {
        if (match.knowledge.difficulty === 'basic') {
          match.score *= 1.3;
        }
        // 检查是否有未掌握的依赖
        if (match.knowledge.dependencies && match.knowledge.dependencies.length > 0) {
          match.score *= 0.8; // 降低有依赖的高级知识点权重
        }
      });
    }

    // 为高级用户降低基础知识点权重
    if (userLevel === 'advanced') {
      adjusted.forEach(match => {
        if (match.knowledge.difficulty === 'basic') {
          match.score *= 0.7;
        }
        if (match.knowledge.difficulty === 'advanced') {
          match.score *= 1.2;
        }
      });
    }

    // 重新排序
    adjusted.sort((a, b) => b.score - a.score);

    // 限制返回数量，保留最相关的
    return adjusted.slice(0, 10);
  }

  /**
   * 获取知识点的依赖链
   */
  getDependencyChain(knowledgeId: string): string[] {
    const chain: string[] = [];
    const visited = new Set<string>();
    
    const traverse = (id: string) => {
      if (visited.has(id)) return;
      visited.add(id);
      
      const knowledge = this.knowledgeBase.get(id);
      if (!knowledge) return;
      
      if (knowledge.dependencies) {
        for (const depId of knowledge.dependencies) {
          traverse(depId);
        }
      }
      
      chain.push(id);
    };
    
    traverse(knowledgeId);
    return chain;
  }

  /**
   * 获取推荐的学习路径
   */
  getRecommendedPath(
    primaryKnowledge: string | null,
    userLevel: string
  ): string[] {
    if (!primaryKnowledge) return [];
    
    const chain = this.getDependencyChain(primaryKnowledge);
    
    // 根据用户水平筛选
    if (userLevel === 'advanced') {
      // 高级用户只需要相关的高级知识点
      return chain.filter(id => {
        const knowledge = this.knowledgeBase.get(id);
        return knowledge?.difficulty === 'advanced' || knowledge?.difficulty === 'intermediate';
      });
    }
    
    // 初学者需要完整的学习路径
    return chain;
  }
}
# AST 特征提取与知识点匹配设计

## 概述

本文档定义了 Learn-Linker 插件的 AST 特征提取和知识点匹配系统设计。该系统用于：
1. 从用户选中的代码中提取语法特征
2. 基于特征匹配相关知识点
3. 为 AI 解释提供上下文信息
4. 确保解释内容与推荐知识点的一致性

## 核心架构

### 1. 数据流

```
用户选中代码 
    ↓
[AST 解析器] → 纯特征提取
    ↓
[知识匹配器] → 匹配知识点 + 推断用户水平
    ↓
[统一输出生成器] → AI 上下文 + 知识点链接
    ↓
AI 解释 + 知识推荐（保证一致性）
```

## 数据结构定义

### 1. AST 特征（纯特征，不含知识点）

```typescript
interface AstFeatures {
  // 原子特征（AST 直接提取）
  atomic: {
    syntax: string[];      // ["let", "arrow-function", "async", "await"]
    api: string[];         // ["Array.map", "Promise.all", "fetch"]
    operations: string[];  // ["loop", "conditional", "try-catch"]
  };
  
  // 结构特征（AST 分析得出）
  structural: {
    patterns: string[];    // ["async-await", "promise-chain", "error-handling"]
    nesting: number;       // 嵌套深度
    complexity: number;    // 圈复杂度
  };
  
  // 统计特征（用于推断水平）
  statistical: {
    syntaxDistribution: {
      basic: string[];     // ["var", "if", "for"]
      intermediate: string[]; // ["arrow-function", "destructuring"]  
      advanced: string[];  // ["async", "generator", "proxy"]
    };
    featureCount: {
      basicCount: number;
      intermediateCount: number;
      advancedCount: number;
    };
  };
}
```

### 2. 知识点定义

```typescript
interface KnowledgeDefinition {
  id: string;                    // "js-sec-5-3"
  title: string;                 // "async/await"
  requiredFeatures: string[];    // 必须包含的特征
  optionalFeatures: string[];    // 可选特征（加分项）
  weight: Map<string, number>;   // 特征权重
  difficulty: 'basic' | 'intermediate' | 'advanced';
  dependencies?: string[];       // 前置知识点
  category: string;              // 知识类别
}
```

### 3. 匹配结果

```typescript
interface KnowledgeMatchResult {
  primaryKnowledge: string | null;  // 主要知识点 ID
  allMatches: Array<{
    id: string;
    score: number;
    knowledge: KnowledgeDefinition;
  }>;
  userLevel: 'beginner' | 'intermediate' | 'advanced';
  coverage: {
    basic: number;       // 0-1
    intermediate: number;
    advanced: number;
  };
}
```

### 4. 统一输出

```typescript
interface UnifiedOutput {
  // 给 AI 的上下文
  aiContext: {
    code: string;
    extractedFeatures: AstFeatures;
    userLevel: string;
    primaryTopic: string | null;
    instruction: string;  // 给 AI 的指导
  };
  
  // 知识点链接
  knowledgeLinks: Array<{
    id: string;
    title: string;
    relevance: number;  // 相关度分数
  }>;
}
```

## 核心模块设计

### 1. AST 特征提取器

```typescript
class FeatureExtractor {
  private parser: TreeSitterParser;
  
  async extractFeatures(code: string, language: string): Promise<AstFeatures> {
    // 1. 解析 AST
    const tree = await this.parser.parse(code, language);
    
    // 2. 提取原子特征
    const atomic = this.extractAtomicFeatures(tree);
    
    // 3. 分析结构特征
    const structural = this.analyzeStructuralPatterns(tree);
    
    // 4. 计算统计特征
    const statistical = this.calculateStatistics(atomic, structural);
    
    return { atomic, structural, statistical };
  }
  
  private extractAtomicFeatures(tree: any): AtomicFeatures {
    // 遍历 AST 节点，提取语法元素
    // 识别 API 调用
    // 识别操作类型
  }
  
  private analyzeStructuralPatterns(tree: any): StructuralFeatures {
    // 识别代码模式
    // 计算嵌套深度
    // 评估复杂度
  }
  
  private calculateStatistics(
    atomic: AtomicFeatures,
    structural: StructuralFeatures
  ): StatisticalFeatures {
    // 分类特征难度
    // 统计各级别特征数量
  }
}
```

### 2. 知识点匹配器

```typescript
class KnowledgeMatcher {
  private knowledgeBase: Map<string, KnowledgeDefinition>;
  
  constructor() {
    this.loadKnowledgeDefinitions();
  }
  
  async matchKnowledge(features: AstFeatures): Promise<KnowledgeMatchResult> {
    const matches = [];
    
    // 1. 遍历所有知识点，计算匹配分数
    for (const [id, knowledge] of this.knowledgeBase) {
      const score = this.calculateMatchScore(features, knowledge);
      if (score > 0.5) {  // 阈值
        matches.push({ id, score, knowledge });
      }
    }
    
    // 2. 排序选择主要知识点
    matches.sort((a, b) => b.score - a.score);
    const primaryKnowledge = matches[0]?.id || null;
    
    // 3. 推断用户水平
    const userLevel = this.inferUserLevel(features.statistical);
    
    // 4. 计算知识覆盖度
    const coverage = this.calculateCoverage(features.statistical);
    
    return {
      primaryKnowledge,
      allMatches: matches,
      userLevel,
      coverage
    };
  }
  
  private calculateMatchScore(
    features: AstFeatures,
    knowledge: KnowledgeDefinition
  ): number {
    let score = 0;
    const allFeatures = [
      ...features.atomic.syntax,
      ...features.atomic.api,
      ...features.structural.patterns
    ];
    
    // 检查必需特征
    for (const required of knowledge.requiredFeatures) {
      if (!allFeatures.includes(required)) {
        return 0;  // 缺少必需特征
      }
      score += knowledge.weight.get(required) || 1.0;
    }
    
    // 可选特征加分
    for (const optional of knowledge.optionalFeatures) {
      if (allFeatures.includes(optional)) {
        score += knowledge.weight.get(optional) || 0.5;
      }
    }
    
    return score;
  }
  
  private inferUserLevel(stats: StatisticalFeatures): string {
    const { featureCount } = stats;
    const total = featureCount.basicCount + 
                  featureCount.intermediateCount + 
                  featureCount.advancedCount;
    
    if (total === 0) return 'beginner';
    
    const advancedRatio = featureCount.advancedCount / total;
    const intermediateRatio = featureCount.intermediateCount / total;
    
    if (advancedRatio > 0.5) return 'advanced';
    if (intermediateRatio > 0.5) return 'intermediate';
    return 'beginner';
  }
}
```

### 3. 统一分析器

```typescript
class UnifiedAstAnalyzer {
  private extractor: FeatureExtractor;
  private matcher: KnowledgeMatcher;
  
  async analyzeCode(code: string, language: string): Promise<UnifiedOutput> {
    // Step 1: 提取特征
    const features = await this.extractor.extractFeatures(code, language);
    
    // Step 2: 匹配知识点
    const matchResult = await this.matcher.matchKnowledge(features);
    
    // Step 3: 生成统一输出
    return this.generateUnifiedOutput(code, features, matchResult);
  }
  
  private generateUnifiedOutput(
    code: string,
    features: AstFeatures,
    matchResult: KnowledgeMatchResult
  ): UnifiedOutput {
    const instruction = this.generateAiInstruction(
      matchResult.userLevel,
      matchResult.primaryKnowledge
    );
    
    return {
      aiContext: {
        code,
        extractedFeatures: features,
        userLevel: matchResult.userLevel,
        primaryTopic: matchResult.primaryKnowledge,
        instruction
      },
      knowledgeLinks: matchResult.allMatches.map(m => ({
        id: m.id,
        title: m.knowledge.title,
        relevance: m.score
      }))
    };
  }
  
  private generateAiInstruction(level: string, topic: string | null): string {
    if (!topic) {
      return "解释这段代码的功能";
    }
    
    switch (level) {
      case 'advanced':
        return `用户代码涉及${topic}，这是高级特性。
                假设用户已掌握基础知识，重点解释核心概念和最佳实践。`;
      
      case 'intermediate':
        return `用户代码涉及${topic}。
                简要回顾基础概念，重点解释当前特性的使用方法。`;
      
      default:
        return `用户代码涉及${topic}。
                请从基础概念开始，详细解释每个部分的作用。`;
    }
  }
}
```

## 知识点配置示例

```typescript
// knowledgeBase.config.ts
export const knowledgeDefinitions: KnowledgeDefinition[] = [
  {
    id: "js-sec-5-3",
    title: "async/await 异步编程",
    requiredFeatures: ["async", "await"],
    optionalFeatures: ["try-catch", "promise", "error-handling"],
    weight: new Map([
      ["async", 1.0],
      ["await", 1.0],
      ["try-catch", 0.3],
      ["error-handling", 0.3]
    ]),
    difficulty: "advanced",
    dependencies: ["js-sec-5-2"],  // Promise
    category: "异步编程"
  },
  
  {
    id: "js-sec-1-3-3",
    title: "for 循环",
    requiredFeatures: ["for-loop"],
    optionalFeatures: ["array-access", "increment", "comparison"],
    weight: new Map([
      ["for-loop", 1.0],
      ["array-access", 0.5],
      ["increment", 0.3]
    ]),
    difficulty: "basic",
    dependencies: [],
    category: "控制流"
  },
  
  {
    id: "js-sec-2-1-4",
    title: "数组转换方法 (map/filter/reduce)",
    requiredFeatures: ["array-method"],
    optionalFeatures: ["arrow-function", "return", "callback"],
    weight: new Map([
      ["Array.map", 1.0],
      ["Array.filter", 1.0],
      ["Array.reduce", 1.0],
      ["arrow-function", 0.5]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-2-1-1", "js-sec-3-1-1"],
    category: "数组操作"
  }
];
```

## Tree-sitter 集成

### 1. 支持的语言

- JavaScript
- TypeScript  
- Python
- Java (扩展)
- Go (扩展)
- Rust (扩展)

### 2. 语言特定的特征映射

```typescript
// featureMappings.ts
export const languageMappings = {
  javascript: {
    syntaxMap: {
      "function_declaration": "function",
      "arrow_function": "arrow-function",
      "async_function": "async",
      "await_expression": "await"
    },
    patternMap: {
      "async_function + await_expression": "async-await",
      "try_statement + catch_clause": "error-handling"
    }
  },
  
  python: {
    syntaxMap: {
      "function_definition": "function",
      "async_function_definition": "async",
      "await": "await",
      "list_comprehension": "list-comprehension"
    },
    patternMap: {
      "async_function_definition + await": "async-await",
      "try_statement + except_clause": "error-handling"
    }
  }
};
```

## 实施计划

### Phase 1: 基础实现（第1周）
1. ✅ 设计文档编写
2. Tree-sitter 基础集成
3. JavaScript/TypeScript 特征提取器

### Phase 2: 知识匹配（第2周）
1. 知识点配置系统
2. 匹配算法实现
3. 用户水平推断

### Phase 3: AI 集成（第3周）
1. 统一输出生成器
2. AI 上下文优化
3. 知识点链接展示

### Phase 4: 多语言支持（第4周）
1. Python 支持
2. 其他语言扩展
3. 性能优化

## 性能考虑

1. **缓存策略**：缓存已解析的 AST 和特征
2. **增量解析**：利用 Tree-sitter 的增量解析能力
3. **异步处理**：特征提取和匹配异步执行
4. **限制范围**：只分析选中代码及上下文

## 测试策略

1. **单元测试**：各模块独立测试
2. **集成测试**：完整流程测试
3. **性能测试**：大文件处理性能
4. **准确性测试**：知识点匹配准确率

## 成功指标

1. 知识点匹配准确率 > 85%
2. 用户水平推断准确率 > 80%
3. AI 解释与推荐知识点一致性 > 95%
4. 特征提取响应时间 < 100ms
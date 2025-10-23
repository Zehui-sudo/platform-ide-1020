import { TreeSitterParser } from './TreeSitterParser';
import { AstFeatures, AtomicFeatures, StructuralFeatures, StatisticalFeatures } from './types/ast.types';
import { getSyntaxMapping, getPatternMapping, getFeatureDifficulty } from './config/featureMappings';

/**
 * AST 特征提取器
 */
export class FeatureExtractor {
  private parser: TreeSitterParser;

  constructor(parser: TreeSitterParser) {
    this.parser = parser;
  }

  /**
   * 提取代码特征
   */
  async extractFeatures(code: string, language: string): Promise<AstFeatures> {
    // 解析 AST
    const tree = await this.parser.parse(code, language);
    const root = tree.rootNode;

    // 提取各类特征
    const atomic = this.extractAtomicFeatures(root, code, language);
    const structural = this.extractStructuralFeatures(root, code);
    const statistical = this.calculateStatistics(atomic, structural);

    return {
      atomic,
      structural,
      statistical
    };
  }

  /**
   * 提取原子特征
   */
  private extractAtomicFeatures(
    root: any,
    code: string,
    language: string
  ): AtomicFeatures {
    const syntax: Set<string> = new Set();
    const api: Set<string> = new Set();
    const operations: Set<string> = new Set();

    const syntaxMapping = getSyntaxMapping(language);

    // 遍历 AST 节点
    this.parser.traverseNode(root, (node) => {
      // 映射语法特征
      const mappedSyntax = syntaxMapping[node.type];
      if (mappedSyntax) {
        syntax.add(mappedSyntax);
      }

      // 识别操作类型
      this.classifyOperation(node, operations);

      // 识别 API 调用
      this.detectApiCalls(node, code, api);
    });

    return {
      syntax: Array.from(syntax),
      api: Array.from(api),
      operations: Array.from(operations)
    };
  }

  /**
   * 分类操作类型
   */
  private classifyOperation(node: any, operations: Set<string>): void {
    const operationTypes: Record<string, string> = {
      // 控制流
      'if_statement': 'conditional',
      'else_clause': 'conditional',
      'ternary_expression': 'conditional',
      'conditional_expression': 'conditional',
      'switch_statement': 'switch',
      'switch_case': 'switch-case',
      
      // 循环
      'for_statement': 'loop',
      'for_in_statement': 'loop',
      'for_of_statement': 'loop',
      'while_statement': 'loop',
      'do_statement': 'loop',
      
      // 跳转
      'break_statement': 'break',
      'continue_statement': 'continue',
      'return_statement': 'return',
      
      // 异常
      'try_statement': 'try-catch',
      'catch_clause': 'error-handling',
      'throw_statement': 'throw',
      
      // 其他
      'assignment_expression': 'assignment',
      'update_expression': 'increment'
    };

    const operation = operationTypes[node.type];
    if (operation) {
      operations.add(operation);
    }
  }

  /**
   * 检测 API 调用
   */
  private detectApiCalls(
    node: any,
    code: string,
    api: Set<string>
  ): void {
    // 检测方法调用
    if (node.type === 'call_expression') {
      const text = this.parser.getNodeText(node, code);
      
      // JavaScript 内置 API
      const jsApis = [
        // Array methods
        'Array.from', 'Array.isArray', 'Array.of',
        '.map(', '.filter(', '.reduce(', '.forEach(', '.find(',
        '.some(', '.every(', '.includes(', '.indexOf(', '.push(',
        '.pop(', '.shift(', '.unshift(', '.slice(', '.splice(',
        '.sort(', '.reverse(', '.join(', '.concat(', '.flat(',
        
        // Object methods
        'Object.keys(', 'Object.values(', 'Object.entries(',
        'Object.assign(', 'Object.create(', 'Object.freeze(',
        
        // Promise
        'Promise.all(', 'Promise.race(', 'Promise.resolve(',
        'Promise.reject(', '.then(', '.catch(', '.finally(',
        
        // String methods
        '.substring(', '.substr(', '.slice(', '.split(',
        '.replace(', '.trim(', '.toLowerCase(', '.toUpperCase(',
        
        // Web APIs
        'fetch(', 'addEventListener(', 'removeEventListener(',
        'querySelector(', 'querySelectorAll(', 'getElementById(',
        'getElementsByClassName(', 'createElement(',
        
        // Fetch response helpers (detect response.json())
        '.json(',
        
        // Console
        'console.log(', 'console.error(', 'console.warn(',
        
        // Timer
        'setTimeout(', 'setInterval(', 'clearTimeout(', 'clearInterval(',
        
        // JSON
        'JSON.parse(', 'JSON.stringify(',
        
        // Math
        'Math.max(', 'Math.min(', 'Math.random(', 'Math.floor(',
        'Math.ceil(', 'Math.round(', 'Math.abs(',
        
        // Storage
        'localStorage.getItem(', 'localStorage.setItem(',
        'sessionStorage.getItem(', 'sessionStorage.setItem(',
        
        // Abort / Request primitives (network tooling)
        'AbortController(', 'Request(', 'Response(', 'Headers(',
        
        // Dynamic import (pattern)
        'import('
      ];

      // 检查是否包含这些 API
      for (const apiPattern of jsApis) {
        if (text.includes(apiPattern)) {
          // 提取 API 名称
          const apiName = apiPattern.replace('(', '').trim();
          api.add(apiName);
        }
      }
    }

    // 检测 new 表达式
    if (node.type === 'new_expression') {
      const text = this.parser.getNodeText(node, code);
      
      const constructors = [
        'Promise', 'Date', 'Error', 'Map', 'Set',
        'WeakMap', 'WeakSet', 'RegExp', 'Array', 'Object'
      ];
      
      for (const ctor of constructors) {
        if (text.includes(`new ${ctor}`)) {
          api.add(ctor);
        }
      }
    }
  }

  /**
   * 提取结构特征
   */
  private extractStructuralFeatures(
    root: any,
    code: string
  ): StructuralFeatures {
    return {
      patterns: this.parser.detectPatterns(root, code),
      nesting: this.parser.calculateNestingDepth(root),
      complexity: this.parser.calculateComplexity(root)
    };
  }

  /**
   * 计算统计特征
   */
  private calculateStatistics(
    atomic: AtomicFeatures,
    structural: StructuralFeatures
  ): StatisticalFeatures {
    const syntaxDistribution = {
      basic: [] as string[],
      intermediate: [] as string[],
      advanced: [] as string[]
    };

    // 分类语法特征
    for (const feature of atomic.syntax) {
      const difficulty = getFeatureDifficulty(feature);
      syntaxDistribution[difficulty].push(feature);
    }

    // 分类 API 特征
    for (const apiCall of atomic.api) {
      const difficulty = this.getApiDifficulty(apiCall);
      syntaxDistribution[difficulty].push(apiCall);
    }

    // 分类模式特征
    for (const pattern of structural.patterns) {
      const difficulty = this.getPatternDifficulty(pattern);
      syntaxDistribution[difficulty].push(pattern);
    }

    // 计算各级别计数
    const featureCount = {
      basicCount: syntaxDistribution.basic.length,
      intermediateCount: syntaxDistribution.intermediate.length,
      advancedCount: syntaxDistribution.advanced.length
    };

    return {
      syntaxDistribution,
      featureCount
    };
  }

  /**
   * 判断 API 的难度级别
   */
  private getApiDifficulty(api: string): 'basic' | 'intermediate' | 'advanced' {
    const basicApis = [
      'console.log', 'console.error', 'alert',
      '.push', '.pop', '.length', '.toString',
      'getElementById', 'getElementsByClassName'
    ];
    
    const advancedApis = [
      'Promise.all', 'Promise.race', 'Proxy', 'Reflect',
      'WeakMap', 'WeakSet', 'Generator', 'Symbol',
      '.reduce', 'Object.defineProperty'
    ];
    
    if (basicApis.some(b => api.includes(b))) {
      return 'basic';
    }
    if (advancedApis.some(a => api.includes(a))) {
      return 'advanced';
    }
    return 'intermediate';
  }

  /**
   * 判断模式的难度级别
   */
  private getPatternDifficulty(pattern: string): 'basic' | 'intermediate' | 'advanced' {
    const advancedPatterns = [
      'async-await', 'generator', 'closure',
      'higher-order-function', 'currying'
    ];
    
    const intermediatePatterns = [
      'promise-chain', 'array-pipeline', 'error-handling',
      'destructuring', 'template-literal'
    ];
    
    if (advancedPatterns.includes(pattern)) {
      return 'advanced';
    }
    if (intermediatePatterns.includes(pattern)) {
      return 'intermediate';
    }
    return 'basic';
  }
}

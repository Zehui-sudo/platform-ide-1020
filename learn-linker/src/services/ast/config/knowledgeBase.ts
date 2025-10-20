import { KnowledgeDefinition } from '../types/ast.types';

/**
 * JavaScript 知识点定义库
 */
export const knowledgeDefinitions: KnowledgeDefinition[] = [
  // ========== 异步编程 ==========
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
    id: "js-sec-5-2",
    title: "Promise 基础",
    requiredFeatures: ["promise"],
    optionalFeatures: ["then", "catch", "finally", "promise-chain"],
    weight: new Map([
      ["promise", 1.0],
      ["then", 0.8],
      ["catch", 0.5],
      ["promise-chain", 0.6]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-5-1"],
    category: "异步编程"
  },
  
  // ========== 控制流 ==========
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
    id: "js-sec-1-3-1",
    title: "if-else 条件判断",
    requiredFeatures: ["conditional"],
    optionalFeatures: ["comparison", "logical-operator"],
    weight: new Map([
      ["conditional", 1.0],
      ["comparison", 0.4],
      ["logical-operator", 0.3]
    ]),
    difficulty: "basic",
    dependencies: [],
    category: "控制流"
  },
  
  // ========== 数组操作 ==========
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
  },
  
  {
    id: "js-sec-2-1-3",
    title: "数组遍历 (forEach)",
    requiredFeatures: ["Array.forEach"],
    optionalFeatures: ["arrow-function", "callback"],
    weight: new Map([
      ["Array.forEach", 1.0],
      ["arrow-function", 0.4],
      ["callback", 0.3]
    ]),
    difficulty: "basic",
    dependencies: ["js-sec-2-1-1"],
    category: "数组操作"
  },
  
  // ========== 函数 ==========
  {
    id: "js-sec-1-4-3",
    title: "箭头函数",
    requiredFeatures: ["arrow-function"],
    optionalFeatures: ["implicit-return", "this-binding"],
    weight: new Map([
      ["arrow-function", 1.0],
      ["implicit-return", 0.4],
      ["this-binding", 0.3]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-1-4-1"],
    category: "函数"
  },
  
  {
    id: "js-sec-3-1-3",
    title: "闭包",
    requiredFeatures: ["closure"],
    optionalFeatures: ["nested-function", "lexical-scope"],
    weight: new Map([
      ["closure", 1.0],
      ["nested-function", 0.6],
      ["lexical-scope", 0.5]
    ]),
    difficulty: "advanced",
    dependencies: ["js-sec-1-4-1", "js-sec-1-1-5"],
    category: "函数进阶"
  },
  
  // ========== 变量与类型 ==========
  {
    id: "js-sec-1-1-1",
    title: "变量声明 (var/let/const)",
    requiredFeatures: ["variable-declaration"],
    optionalFeatures: ["let", "const", "var"],
    weight: new Map([
      ["let", 0.8],
      ["const", 0.8],
      ["var", 0.4]
    ]),
    difficulty: "basic",
    dependencies: [],
    category: "基础"
  },
  
  {
    id: "js-sec-1-1-5",
    title: "作用域与提升",
    requiredFeatures: ["scope"],
    optionalFeatures: ["hoisting", "block-scope", "function-scope"],
    weight: new Map([
      ["scope", 1.0],
      ["hoisting", 0.7],
      ["block-scope", 0.5]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-1-1-1"],
    category: "基础"
  },
  
  // ========== 对象与类 ==========
  {
    id: "js-sec-4-2-1",
    title: "ES6 类",
    requiredFeatures: ["class"],
    optionalFeatures: ["constructor", "method", "extends", "super"],
    weight: new Map([
      ["class", 1.0],
      ["constructor", 0.6],
      ["extends", 0.8],
      ["super", 0.5]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-2-2-1"],
    category: "面向对象"
  },
  
  // ========== 错误处理 ==========
  {
    id: "js-sec-7-3-1",
    title: "try-catch-finally",
    requiredFeatures: ["try-catch"],
    optionalFeatures: ["finally", "throw", "error-object"],
    weight: new Map([
      ["try-catch", 1.0],
      ["finally", 0.4],
      ["throw", 0.5]
    ]),
    difficulty: "intermediate",
    dependencies: [],
    category: "错误处理"
  },
  
  // ========== ES6+ 特性 ==========
  {
    id: "js-sec-7-1-1",
    title: "解构赋值",
    requiredFeatures: ["destructuring"],
    optionalFeatures: ["object-destructuring", "array-destructuring", "default-value"],
    weight: new Map([
      ["destructuring", 1.0],
      ["object-destructuring", 0.6],
      ["array-destructuring", 0.6]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-2-2-1", "js-sec-2-1-1"],
    category: "ES6+特性"
  },
  
  {
    id: "js-sec-7-1-2",
    title: "展开运算符",
    requiredFeatures: ["spread"],
    optionalFeatures: ["rest", "array-spread", "object-spread"],
    weight: new Map([
      ["spread", 1.0],
      ["rest", 0.5],
      ["array-spread", 0.4],
      ["object-spread", 0.4]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-2-1-1", "js-sec-2-2-1"],
    category: "ES6+特性"
  },
  
  // ========== Web API ==========
  {
    id: "js-sec-8-1-1",
    title: "fetch 网络请求",
    requiredFeatures: ["fetch"],
    optionalFeatures: ["promise", "async-await", "json", "headers"],
    weight: new Map([
      ["fetch", 1.0],
      ["promise", 0.5],
      ["async-await", 0.6],
      ["json", 0.3]
    ]),
    difficulty: "intermediate",
    dependencies: ["js-sec-5-2"],
    category: "网络请求"
  },
  
  {
    id: "js-sec-6-2-1",
    title: "事件监听",
    requiredFeatures: ["addEventListener"],
    optionalFeatures: ["event-handler", "event-object", "preventDefault"],
    weight: new Map([
      ["addEventListener", 1.0],
      ["event-handler", 0.5],
      ["event-object", 0.4]
    ]),
    difficulty: "basic",
    dependencies: ["js-sec-1-4-1"],
    category: "DOM与事件"
  },
  
  // ========== 模块化 ==========
  {
    id: "js-sec-7-2-1",
    title: "ES6 模块 (import/export)",
    requiredFeatures: ["import"],
    optionalFeatures: ["export", "default-export", "named-export"],
    weight: new Map([
      ["import", 1.0],
      ["export", 1.0],
      ["default-export", 0.5],
      ["named-export", 0.5]
    ]),
    difficulty: "intermediate",
    dependencies: [],
    category: "模块化"
  }
];

/**
 * 根据知识点 ID 获取定义
 */
export function getKnowledgeById(id: string): KnowledgeDefinition | undefined {
  return knowledgeDefinitions.find(k => k.id === id);
}

/**
 * 根据类别获取知识点
 */
export function getKnowledgeByCategory(category: string): KnowledgeDefinition[] {
  return knowledgeDefinitions.filter(k => k.category === category);
}

/**
 * 获取所有类别
 */
export function getAllCategories(): string[] {
  return [...new Set(knowledgeDefinitions.map(k => k.category))];
}
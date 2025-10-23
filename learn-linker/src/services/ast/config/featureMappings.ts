import { LanguageMapping } from '../types/ast.types';

// 先定义 JavaScript 映射
const javascriptMapping: LanguageMapping = {
    syntaxMap: {
      // 变量声明
      'variable_declaration': 'variable-declaration',
      'const': 'const',
      'let': 'let',
      'var': 'var',
      
      // 函数
      'function_declaration': 'function',
      'function_expression': 'function',
      'arrow_function': 'arrow-function',
      'async_function': 'async',
      'async_arrow_function': 'async',
      'generator_function': 'generator',
      
      // 异步
      'await_expression': 'await',
      'promise': 'promise',
      'new_expression': 'new',
      
      // 控制流
      'if_statement': 'conditional',
      'ternary_expression': 'conditional',
      'switch_statement': 'switch',
      'for_statement': 'for-loop',
      'for_in_statement': 'for-in',
      'for_of_statement': 'for-of',
      'while_statement': 'while-loop',
      'do_statement': 'do-while',
      'break_statement': 'break',
      'continue_statement': 'continue',
      
      // 异常处理
      'try_statement': 'try-catch',
      'catch_clause': 'catch',
      'finally_clause': 'finally',
      'throw_statement': 'throw',
      
      // 类与对象
      'class_declaration': 'class',
      'constructor': 'constructor',
      'method_definition': 'method',
      'extends_clause': 'extends',
      'super': 'super',
      'object_expression': 'object-literal',
      'property': 'property',
      
      // 解构和展开
      'object_pattern': 'object-destructuring',
      'array_pattern': 'array-destructuring',
      'spread_element': 'spread',
      'rest_pattern': 'rest',
      
      // 模块
      'import_statement': 'import',
      'export_statement': 'export',
      'import_specifier': 'named-import',
      'export_specifier': 'named-export',
      'export_default': 'default-export',
      
      // 操作符
      'assignment_expression': 'assignment',
      'binary_expression': 'binary-operator',
      'unary_expression': 'unary-operator',
      'update_expression': 'increment',
      
      // 其他
      'template_literal': 'template-literal',
      'jsx_element': 'jsx',
      'jsx_fragment': 'jsx-fragment',
      'return_statement': 'return',
      'yield_expression': 'yield'
    },
    
    patternMap: {
      // 异步模式
      'async_function + await_expression': 'async-await',
      'promise + then': 'promise-chain',
      'try_statement + catch_clause': 'error-handling',
      'try_statement + finally_clause': 'cleanup-pattern',
      
      // 函数模式
      'arrow_function + implicit_return': 'concise-arrow',
      'function + return function': 'higher-order-function',
      'function + nested_function': 'closure',
      
      // 数组操作模式
      'Array.map + arrow_function': 'functional-array',
      'Array.filter + Array.map': 'array-pipeline',
      'Array.reduce + accumulator': 'reduce-pattern',
      
      // React 模式
      'useState + setState': 'react-state',
      'useEffect + dependency_array': 'react-effect',
      'jsx_element + map': 'react-list-rendering',
      
      // 事件处理
      'addEventListener + arrow_function': 'event-handler',
      'addEventListener + preventDefault': 'form-handling'
    }
};

// TypeScript 映射（继承 JavaScript）
const typescriptMapping: LanguageMapping = {
    syntaxMap: {
      // TypeScript 特有
      'type_annotation': 'type-annotation',
      'interface_declaration': 'interface',
      'type_alias_declaration': 'type-alias',
      'enum_declaration': 'enum',
      'generic_type': 'generic',
      'type_parameter': 'type-parameter',
      'as_expression': 'type-assertion',
      'satisfies_expression': 'satisfies',
      'readonly': 'readonly',
      'abstract_class': 'abstract-class',
      'decorator': 'decorator',
      'namespace': 'namespace',
      
      // 继承 JavaScript 的映射
      ...javascriptMapping.syntaxMap
    },
    
    patternMap: {
      // TypeScript 特有模式
      'interface + implements': 'interface-implementation',
      'generic + constraint': 'generic-constraint',
      'type_guard + narrowing': 'type-narrowing',
      'discriminated_union': 'discriminated-union',
      'decorator + class': 'class-decorator',
      'decorator + method': 'method-decorator',
      
      // 继承 JavaScript 的模式
      ...javascriptMapping.patternMap
    }
};

// Python 映射
const pythonMapping: LanguageMapping = {
    syntaxMap: {
      // 函数
      'function_definition': 'function',
      'lambda': 'lambda',
      'async_function_definition': 'async',
      'decorator': 'decorator',
      
      // 类
      'class_definition': 'class',
      '__init__': 'constructor',
      'method': 'method',
      'classmethod': 'class-method',
      'staticmethod': 'static-method',
      
      // 控制流
      'if_statement': 'conditional',
      'elif': 'elif',
      'for_statement': 'for-loop',
      'while_statement': 'while-loop',
      'break_statement': 'break',
      'continue_statement': 'continue',
      'match_statement': 'pattern-matching',
      
      // 异常
      'try_statement': 'try-except',
      'except_clause': 'except',
      'finally_clause': 'finally',
      'raise_statement': 'raise',
      'with_statement': 'context-manager',
      
      // 异步
      'await': 'await',
      'async_for': 'async-for',
      'async_with': 'async-with',
      
      // 数据结构
      'list_comprehension': 'list-comprehension',
      'dictionary_comprehension': 'dict-comprehension',
      'set_comprehension': 'set-comprehension',
      'generator_expression': 'generator-expression',
      
      // 导入
      'import_statement': 'import',
      'import_from_statement': 'from-import',
      
      // 其他
      'yield': 'yield',
      'assert_statement': 'assert',
      'global': 'global',
      'nonlocal': 'nonlocal',
      'f_string': 'f-string'
    },
    
    patternMap: {
      // Python 模式
      'async_function_definition + await': 'async-await',
      'with_statement + as': 'context-manager-pattern',
      'try_statement + except_clause': 'error-handling',
      'list_comprehension + if': 'filtered-comprehension',
      'decorator + function': 'decorated-function',
      '__init__ + self': 'class-initialization',
      'yield + generator': 'generator-pattern'
    }
};

/**
 * 语言特定的 AST 节点类型到特征的映射
 */
export const languageMappings: Record<string, LanguageMapping> = {
  javascript: javascriptMapping,
  typescript: typescriptMapping,
  tsx: typescriptMapping,
  python: pythonMapping
};

/**
 * 获取语言的语法特征映射
 */
export function getSyntaxMapping(language: string): Record<string, string> {
  const mapping = languageMappings[language];
  if (!mapping) {
    console.warn(`No mapping found for language: ${language}`);
    return {};
  }
  return mapping.syntaxMap;
}

/**
 * 获取语言的模式映射
 */
export function getPatternMapping(language: string): Record<string, string> {
  const mapping = languageMappings[language];
  if (!mapping) {
    console.warn(`No pattern mapping found for language: ${language}`);
    return {};
  }
  return mapping.patternMap;
}

/**
 * 难度分类规则
 */
export const difficultyClassification = {
  basic: [
    'variable-declaration', 'var', 'let', 'const',
    'function', 'conditional', 'for-loop', 'while-loop',
    'object-literal', 'array-literal', 'property',
    'assignment', 'comparison', 'logical-operator'
  ],
  intermediate: [
    'arrow-function', 'template-literal', 'destructuring',
    'spread', 'rest', 'class', 'extends', 'try-catch',
    'promise', 'import', 'export', 'array-method'
  ],
  advanced: [
    'async', 'await', 'generator', 'yield', 'proxy',
    'reflect', 'symbol', 'closure', 'higher-order-function',
    'decorator', 'type-annotation', 'generic'
  ]
};

/**
 * 判断特征的难度级别
 */
export function getFeatureDifficulty(feature: string): 'basic' | 'intermediate' | 'advanced' {
  if (difficultyClassification.basic.includes(feature)) {
    return 'basic';
  }
  if (difficultyClassification.intermediate.includes(feature)) {
    return 'intermediate';
  }
  if (difficultyClassification.advanced.includes(feature)) {
    return 'advanced';
  }
  return 'basic'; // 默认为基础
}

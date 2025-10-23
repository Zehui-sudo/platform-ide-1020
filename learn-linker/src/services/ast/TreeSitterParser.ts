import * as vscode from 'vscode';
import { Parser, Language } from 'web-tree-sitter';
import * as path from 'path';
import * as fs from 'fs';
import { SupportedLanguage } from './types/ast.types';

/**
 * Tree-sitter 解析器封装
 */
export class TreeSitterParser {
  private parser: any | null = null;
  private languages: Map<string, any> = new Map();
  private initialized = false;
  private initPromise: Promise<void> | null = null;

  /**
   * 初始化解析器
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }
    
    if (!this.initPromise) {
      this.initPromise = this.doInitialize();
    }
    
    await this.initPromise;
  }

  private async doInitialize(): Promise<void> {
    try {
      // 初始化 Tree-sitter（指定本地 runtime wasm 路径，去掉对 CDN 的依赖）
      const runtimeWasmPath = this.getRuntimeWasmPath();
      await Parser.init({
        locateFile: (_scriptName: string) => runtimeWasmPath
      });
      this.parser = new Parser();
      
      // 加载语言 WASM 文件
      await this.loadLanguages();
      
      this.initialized = true;
      console.log('Tree-sitter parser initialized');
    } catch (error) {
      console.error('Failed to initialize Tree-sitter:', error);
      throw error;
    }
  }

  /**
   * 加载支持的语言
   */
  private async loadLanguages(): Promise<void> {
    // 尝试获取扩展路径
    const extensionPath = this.getExtensionRoot();

    // 语言 WASM 文件映射
    const languageFiles: Record<SupportedLanguage, string> = {
      javascript: 'tree-sitter-javascript.wasm',
      typescript: 'tree-sitter-typescript.wasm',
      tsx: 'tree-sitter-tsx.wasm',
      python: 'tree-sitter-python.wasm',
      java: 'tree-sitter-java.wasm',
      go: 'tree-sitter-go.wasm',
      rust: 'tree-sitter-rust.wasm'
    };

    // 优先加载常用语言
    const priorityLanguages: SupportedLanguage[] = ['javascript', 'typescript', 'tsx', 'python'];
    
    for (const lang of priorityLanguages) {
      try {
        await this.loadLanguage(lang, languageFiles[lang]);
      } catch (error) {
        console.warn(`Failed to load language ${lang}:`, error);
      }
    }
  }

  /**
   * 加载单个语言
   */
  private async loadLanguage(name: SupportedLanguage, fileName: string): Promise<void> {
    try {
      const wasmPath = this.getLanguageWasmPath(fileName);
      if (!wasmPath) {
        console.warn(`Language wasm not found for ${name} (${fileName}).`);
        return;
      }
      const language = await Language.load(wasmPath);
      this.languages.set(name, language);
      console.log(`Loaded language: ${name} from ${wasmPath}`);
    } catch (error) {
      console.error(`Failed to load language ${name}:`, error);
      // 对于非关键语言，不抛出错误
    }
  }

  /**
   * 解析代码
   */
  async parse(code: string, language: string): Promise<any> {
    if (!this.initialized) {
      await this.initialize();
    }

    if (!this.parser) {
      throw new Error('Parser not initialized');
    }

    // 映射 VSCode 语言 ID 到 Tree-sitter 语言
    const langMapping: Record<string, SupportedLanguage> = {
      'javascript': 'javascript',
      'javascriptreact': 'javascript',
      'typescript': 'typescript',
      'typescriptreact': 'tsx',
      'python': 'python',
      'java': 'java',
      'go': 'go',
      'rust': 'rust'
    };

    const treeSitterLang = langMapping[language] || 'javascript';
    const lang = this.languages.get(treeSitterLang);

    if (!lang) {
      console.warn(`Language ${treeSitterLang} not loaded, falling back to JavaScript`);
      const fallbackLang = this.languages.get('javascript');
      if (!fallbackLang) {
        throw new Error('No language loaded (no local wasm available).');
      }
      this.parser.setLanguage(fallbackLang);
    } else {
      this.parser.setLanguage(lang);
    }

    return this.parser.parse(code);
  }

  /**
   * 遍历 AST 节点
   */
  traverseNode(
    node: any,
    callback: (node: any) => void
  ): void {
    callback(node);
    
    for (let i = 0; i < node.childCount; i++) {
      const child = node.child(i);
      if (child) {
        this.traverseNode(child, callback);
      }
    }
  }

  /**
   * 查找特定类型的节点
   */
  findNodesByType(
    root: any,
    nodeType: string
  ): any[] {
    const nodes: any[] = [];
    
    this.traverseNode(root, (node) => {
      if (node.type === nodeType) {
        nodes.push(node);
      }
    });
    
    return nodes;
  }

  /**
   * 获取节点的源代码
   */
  getNodeText(node: any, code: string): string {
    return code.substring(node.startIndex, node.endIndex);
  }

  /**
   * 计算嵌套深度
   */
  calculateNestingDepth(root: any): number {
    let maxDepth = 0;
    
    const calculateDepth = (node: any, depth: number): void => {
      maxDepth = Math.max(maxDepth, depth);
      
      for (let i = 0; i < node.childCount; i++) {
        const child = node.child(i);
        if (child && this.isNestingNode(child)) {
          calculateDepth(child, depth + 1);
        } else if (child) {
          calculateDepth(child, depth);
        }
      }
    };
    
    calculateDepth(root, 0);
    return maxDepth;
  }

  /**
   * 判断是否是嵌套节点
   */
  private isNestingNode(node: any): boolean {
    const nestingTypes = [
      'function_declaration',
      'function_expression',
      'arrow_function',
      'if_statement',
      'for_statement',
      'while_statement',
      'try_statement',
      'block_statement',
      'class_declaration'
    ];
    
    return nestingTypes.includes(node.type);
  }

  /**
   * 计算圈复杂度
   */
  calculateComplexity(root: any): number {
    let complexity = 1; // 基础复杂度
    
    this.traverseNode(root, (node) => {
      // 增加复杂度的节点类型
      const complexityNodes = [
        'if_statement',
        'else_clause',
        'switch_case',
        'for_statement',
        'while_statement',
        'do_statement',
        'catch_clause',
        'conditional_expression', // 三元运算符
        'logical_expression' // && ||
      ];
      
      if (complexityNodes.includes(node.type)) {
        complexity++;
      }
    });
    
    return complexity;
  }

  /**
   * 检测代码模式
   */
  detectPatterns(root: any, code: string): string[] {
    const patterns: string[] = [];
    
    // 检测 async/await 模式
    const asyncFunctions = this.findNodesByType(root, 'async_function');
    const asyncArrows = this.findNodesByType(root, 'async_arrow_function');
    const awaitExpressions = this.findNodesByType(root, 'await_expression');
    
    if ((asyncFunctions.length > 0 || asyncArrows.length > 0) && awaitExpressions.length > 0) {
      patterns.push('async-await');
    }
    
    // 检测 Promise 链
    const memberExpressions = this.findNodesByType(root, 'member_expression');
    const promiseChain = memberExpressions.some(node => {
      const text = this.getNodeText(node, code);
      return text.includes('.then') || text.includes('.catch') || text.includes('.finally');
    });
    
    if (promiseChain) {
      patterns.push('promise-chain');
    }
    
    // 检测错误处理模式
    const tryStatements = this.findNodesByType(root, 'try_statement');
    if (tryStatements.length > 0) {
      patterns.push('error-handling');
    }
    
    // 检测数组方法链
    const callExpressions = this.findNodesByType(root, 'call_expression');
    const arrayMethods = ['map', 'filter', 'reduce', 'forEach', 'find', 'some', 'every'];
    let arrayMethodCount = 0;
    
    callExpressions.forEach(node => {
      const text = this.getNodeText(node, code);
      if (arrayMethods.some(method => text.includes(`.${method}(`))) {
        arrayMethodCount++;
      }
    });
    
    if (arrayMethodCount >= 2) {
      patterns.push('array-pipeline');
    } else if (arrayMethodCount === 1) {
      patterns.push('array-method');
    }
    
    // 检测闭包
    const functions = [...this.findNodesByType(root, 'function_declaration'),
                      ...this.findNodesByType(root, 'function_expression'),
                      ...this.findNodesByType(root, 'arrow_function')];
    
    for (const func of functions) {
      const nestedFunctions = this.findNodesByType(func, 'function_declaration')
        .concat(this.findNodesByType(func, 'function_expression'))
        .concat(this.findNodesByType(func, 'arrow_function'));
      
      if (nestedFunctions.length > 1) { // 排除自身
        patterns.push('closure');
        break;
      }
    }
    
    return [...new Set(patterns)]; // 去重
  }

  /**
   * 清理资源
   */
  dispose(): void {
    this.parser = null;
    this.languages.clear();
    this.initialized = false;
    this.initPromise = null;
  }

  /**
   * 解析扩展根路径（兼容发布与开发环境）
   */
  private getExtensionRoot(): string {
    const candidates = [
      vscode.extensions.getExtension('platform-ide.learn-linker')?.extensionPath,
      path.resolve(__dirname, '..'), // dist -> extension root
      path.resolve(__dirname, '..', '..') // fallback: parent of root (rare)
    ].filter(Boolean) as string[];

    for (const c of candidates) {
      try {
        if (fs.existsSync(c)) {
          return c;
        }
      } catch {}
    }
    // 最后退回当前目录
    return path.resolve(__dirname, '..');
  }

  /**
   * 获取 runtime wasm 路径（tree-sitter.wasm）
   */
  private getRuntimeWasmPath(): string {
    const root = this.getExtensionRoot();
    const candidates = [
      path.join(root, 'resources', 'wasm', 'tree-sitter.wasm'),
      path.join(path.resolve(__dirname, '..'), 'resources', 'wasm', 'tree-sitter.wasm'),
      path.join(root, 'node_modules', 'web-tree-sitter', 'tree-sitter.wasm'),
      path.resolve(__dirname, '..', '..', 'node_modules', 'web-tree-sitter', 'tree-sitter.wasm')
    ];
    for (const p of candidates) {
      if (fs.existsSync(p)) {
        return p;
      }
    }
    console.error('tree-sitter runtime wasm not found. Tried:\n' + candidates.join('\n'));
    throw new Error('tree-sitter.wasm not found. Please place it under resources/wasm.');
  }

  /**
   * 获取语言 wasm 路径（tree-sitter-<lang>.wasm）
   */
  private getLanguageWasmPath(fileName: string): string | null {
    const root = this.getExtensionRoot();
    const candidates = [
      path.join(root, 'resources', 'wasm', fileName),
      path.join(path.resolve(__dirname, '..'), 'resources', 'wasm', fileName),
      path.join(root, 'node_modules', fileName.startsWith('tree-sitter-') ? fileName.replace('.wasm', '') : '', fileName)
    ];
    for (const p of candidates) {
      if (p && fs.existsSync(p)) {
        return p;
      }
    }
    return null;
  }
}

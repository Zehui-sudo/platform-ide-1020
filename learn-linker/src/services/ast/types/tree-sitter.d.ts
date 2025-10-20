/**
 * 简化的 Tree-sitter 类型定义
 */

declare module 'web-tree-sitter' {
  export interface Point {
    row: number;
    column: number;
  }

  export interface Range {
    startPosition: Point;
    endPosition: Point;
    startIndex: number;
    endIndex: number;
  }

  export interface SyntaxNode {
    type: string;
    text: string;
    startIndex: number;
    endIndex: number;
    startPosition: Point;
    endPosition: Point;
    parent: SyntaxNode | null;
    children: SyntaxNode[];
    childCount: number;
    namedChildCount: number;
    firstChild: SyntaxNode | null;
    firstNamedChild: SyntaxNode | null;
    lastChild: SyntaxNode | null;
    lastNamedChild: SyntaxNode | null;
    nextSibling: SyntaxNode | null;
    nextNamedSibling: SyntaxNode | null;
    previousSibling: SyntaxNode | null;
    previousNamedSibling: SyntaxNode | null;
    
    child(index: number): SyntaxNode | null;
    namedChild(index: number): SyntaxNode | null;
    childForFieldName(fieldName: string): SyntaxNode | null;
    descendantForIndex(index: number): SyntaxNode;
    descendantsOfType(type: string): SyntaxNode[];
    
    isNamed: boolean;
    isError: boolean;
    isMissing: boolean;
  }

  export interface Tree {
    rootNode: SyntaxNode;
    edit(edit: any): void;
    walk(): TreeCursor;
  }

  export interface TreeCursor {
    nodeType: string;
    currentNode: SyntaxNode;
    
    gotoParent(): boolean;
    gotoFirstChild(): boolean;
    gotoNextSibling(): boolean;
  }

  export interface Language {
    // Language methods
  }

  export interface Query {
    // Query methods
  }

  export default class Parser {
    static init(): Promise<void>;
    static Language: {
      load(url: string | Uint8Array): Promise<Language>;
    };

    constructor();
    setLanguage(language: Language | null): void;
    parse(input: string, oldTree?: Tree): Tree;
    getLanguage(): Language | null;
    setTimeoutMicros(timeout: number): void;
    getTimeoutMicros(): number;
    reset(): void;
    getIncludedRanges(): Range[];
    setIncludedRanges(ranges: Range[]): void;
  }
}
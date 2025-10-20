import * as vscode from 'vscode';
import { CodeContext } from './ai/IAiService';

/**
 * 代码上下文收集器
 * 负责收集选中代码的相关上下文信息
 */
export class ContextCollector {
    /**
     * 收集代码上下文
     */
    static async collectContext(
        document: vscode.TextDocument, 
        range: vscode.Range
    ): Promise<CodeContext> {
        const config = vscode.workspace.getConfiguration('learnLinker');
        const enableContext = config.get<boolean>('enableContextCollection', true);
        
        const code = document.getText(range);
        const language = document.languageId;
        
        const context: CodeContext = {
            code,
            language,
            fileName: document.fileName.split('/').pop()
        };

        if (!enableContext) {
            return context;
        }

        // 收集周围代码
        context.surroundingCode = this.getSurroundingCode(document, range);
        
        // 收集导入语句
        context.imports = this.getImports(document);

        return context;
    }

    /**
     * 获取选中代码的上下文（前后各10行）
     */
    private static getSurroundingCode(
        document: vscode.TextDocument, 
        range: vscode.Range
    ): { before: string; after: string } | undefined {
        const contextLines = 10;
        
        // 获取前文
        const startLine = Math.max(0, range.start.line - contextLines);
        const beforeRange = new vscode.Range(
            new vscode.Position(startLine, 0),
            range.start
        );
        const before = document.getText(beforeRange).trim();
        
        // 获取后文
        const endLine = Math.min(document.lineCount - 1, range.end.line + contextLines);
        const afterRange = new vscode.Range(
            range.end,
            new vscode.Position(endLine, document.lineAt(endLine).text.length)
        );
        const after = document.getText(afterRange).trim();

        if (!before && !after) {
            return undefined;
        }

        return { before, after };
    }

    /**
     * 获取文件的导入语句
     */
    private static getImports(document: vscode.TextDocument): string[] {
        const imports: string[] = [];
        const text = document.getText();
        const lines = text.split('\n');
        
        for (const line of lines) {
            const trimmedLine = line.trim();
            
            // JavaScript/TypeScript imports
            if (trimmedLine.startsWith('import ') || 
                trimmedLine.startsWith('const ') && trimmedLine.includes('require(') ||
                trimmedLine.startsWith('export ')) {
                imports.push(trimmedLine);
            }
            // Python imports
            else if (trimmedLine.startsWith('from ') || 
                     trimmedLine.startsWith('import ')) {
                imports.push(trimmedLine);
            }
            // Java imports
            else if (trimmedLine.startsWith('package ') || 
                     trimmedLine.startsWith('import ')) {
                imports.push(trimmedLine);
            }
            // Go imports
            else if (trimmedLine.startsWith('package ') || 
                     trimmedLine.startsWith('import ')) {
                imports.push(trimmedLine);
            }
            // Rust imports
            else if (trimmedLine.startsWith('use ')) {
                imports.push(trimmedLine);
            }
            // C/C++ includes
            else if (trimmedLine.startsWith('#include')) {
                imports.push(trimmedLine);
            }
            
            // 如果已经到了主代码区域，停止搜索
            if (imports.length > 0 && 
                !trimmedLine.startsWith('import') && 
                !trimmedLine.startsWith('from') &&
                !trimmedLine.startsWith('use') &&
                !trimmedLine.startsWith('#include') &&
                trimmedLine.length > 0 &&
                !trimmedLine.startsWith('//') &&
                !trimmedLine.startsWith('/*') &&
                !trimmedLine.startsWith('*')) {
                break;
            }
        }
        
        return imports.slice(0, 20); // 限制最多20个导入
    }

    /**
     * 检测并提取函数或类的完整定义
     */
    static async extractFunctionOrClass(
        document: vscode.TextDocument,
        position: vscode.Position
    ): Promise<string | undefined> {
        // 这个功能需要更复杂的 AST 分析
        // 目前暂时返回 undefined
        // 后续可以集成 tree-sitter 或语言服务器协议
        return undefined;
    }
}
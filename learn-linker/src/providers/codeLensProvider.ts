import * as vscode from 'vscode';
import { WebviewManager } from '../webview/WebviewManager';

export class ExplainCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;
    
    private webviewManager: WebviewManager;

    constructor(webviewManager: WebviewManager) {
        this.webviewManager = webviewManager;
        console.log('[CodeLens] Provider initialized');
        
        // 监听选择变化以刷新 CodeLens
        vscode.window.onDidChangeTextEditorSelection((e) => {
            console.log('[CodeLens] Selection changed:', {
                hasSelection: !e.selections[0].isEmpty,
                selectionText: e.textEditor.document.getText(e.selections[0]).substring(0, 50)
            });
            this._onDidChangeCodeLenses.fire();
        });
    }

    public provideCodeLenses(
        document: vscode.TextDocument,
        _token: vscode.CancellationToken
    ): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
        console.log('[CodeLens] provideCodeLenses called for:', document.fileName);
        
        const codeLenses: vscode.CodeLens[] = [];
        const editor = vscode.window.activeTextEditor;

        if (editor && editor.document === document) {
            const selection = editor.selection;
            console.log('[CodeLens] Current selection:', {
                isEmpty: selection.isEmpty,
                startLine: selection.start.line,
                endLine: selection.end.line,
                text: document.getText(selection).substring(0, 50)
            });
            
            // 只有选择了文本时才显示 CodeLens
            if (!selection.isEmpty) {
                const range = new vscode.Range(selection.start, selection.end);
                const command: vscode.Command = {
                    title: '🤖 获取AI解释',
                    command: 'learn-linker.explainCode',
                    arguments: [document, range]
                };
                
                // 将 CodeLens 放置在选择区域的上方
                const lensRange = new vscode.Range(selection.start.line, 0, selection.start.line, 0);
                codeLenses.push(new vscode.CodeLens(lensRange, command));
                console.log('[CodeLens] Created CodeLens at line:', selection.start.line);
            } else {
                console.log('[CodeLens] No selection, no CodeLens created');
            }
        } else {
            console.log('[CodeLens] Editor document mismatch or no active editor');
        }

        console.log('[CodeLens] Returning', codeLenses.length, 'code lenses');
        return codeLenses;
    }

    public resolveCodeLens(
        codeLens: vscode.CodeLens,
        _token: vscode.CancellationToken
    ): vscode.CodeLens {
        return codeLens;
    }
}
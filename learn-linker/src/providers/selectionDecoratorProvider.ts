import * as vscode from 'vscode';

export class SelectionDecoratorProvider {
    private decorationType: vscode.TextEditorDecorationType;
    private statusBarItem: vscode.StatusBarItem;
    
    constructor() {
        // 创建装饰器类型（暂时禁用内联提示）
        this.decorationType = vscode.window.createTextEditorDecorationType({
            // 移除 after 属性以不显示内联提示
            rangeBehavior: vscode.DecorationRangeBehavior.ClosedOpen
        });

        // 创建状态栏项
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'learn-linker.quickExplain';
        
        // 监听选择变化
        vscode.window.onDidChangeTextEditorSelection(this.updateDecorations, this);
        vscode.window.onDidChangeActiveTextEditor(this.updateDecorations, this);
        
        // 初始更新
        this.updateDecorations();
    }

    private updateDecorations() {
        const editor = vscode.window.activeTextEditor;
        
        if (!editor) {
            this.statusBarItem.hide();
            return;
        }

        const selection = editor.selection;
        
        if (selection.isEmpty) {
            // 清除装饰器
            editor.setDecorations(this.decorationType, []);
            this.statusBarItem.hide();
            console.log('[Decorator] No selection, decorations cleared');
        } else {
            // 清除装饰器（不再显示内联提示）
            editor.setDecorations(this.decorationType, []);
            
            // 更新状态栏
            const selectedText = editor.document.getText(selection);
            const lineCount = selection.end.line - selection.start.line + 1;
            this.statusBarItem.text = `$(sparkle) AI解释 (${lineCount}行)`;
            this.statusBarItem.tooltip = '点击或按 Cmd+Shift+K 获取AI代码解释';
            this.statusBarItem.show();
            
            console.log('[Decorator] Selection detected, status bar updated');
        }
    }

    public dispose() {
        this.decorationType.dispose();
        this.statusBarItem.dispose();
    }
}
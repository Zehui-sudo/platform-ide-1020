import * as vscode from 'vscode';
import * as path from 'path';
import { CodeContext } from '../services/ai/IAiService';
import { AiServiceFactory } from '../services/ai/aiServiceFactory';
import { UnifiedAstAnalyzer } from '../services/ast/UnifiedAnalyzer';

export class WebviewManager {
    private currentPanel: vscode.WebviewPanel | undefined;
    private context: vscode.ExtensionContext;
    private currentAbortController?: AbortController;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    public async showExplanation(codeContext: CodeContext) {
        console.log('[WebviewManager] showExplanation called with code length:', codeContext.code.length);
        const column = vscode.window.activeTextEditor 
            ? vscode.window.activeTextEditor.viewColumn 
            : undefined;

        // 取消之前的生成任务
        this.cancelCurrentGeneration();
        
        // 创建新的 AbortController
        this.currentAbortController = new AbortController();

        // 获取 AI 服务实例
        const aiService = await AiServiceFactory.getService(this.context);

        // 如果面板已存在，则更新内容；否则创建新面板
        if (this.currentPanel) {
            console.log('[WebviewManager] Using existing panel');
            this.currentPanel.reveal(column);
            this.sendMessageToWebview({ 
                type: 'newExplanation', 
                codeContext,
                aiServiceName: aiService.getName()
            });
        } else {
            console.log('[WebviewManager] Creating new panel');
            this.currentPanel = vscode.window.createWebviewPanel(
                'learnLinker.explanation',
                'AI 代码解释',
                vscode.ViewColumn.Beside,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true,
                    localResourceRoots: [
                        vscode.Uri.file(path.join(this.context.extensionPath, 'dist'))
                    ]
                }
            );

            // 先注册来自 webview 的消息监听，避免 ready 竞态
            this.currentPanel.webview.onDidReceiveMessage(
                async message => {
                    switch (message.type) {
                        case 'ready':
                            console.log('[WebviewManager] WebView is ready, sending code');
                            this.sendMessageToWebview({ 
                                type: 'newExplanation', 
                                codeContext,
                                aiServiceName: aiService.getName()
                            });
                            break;
                        case 'generateExplanation':
                            // WebView 请求生成解释
                            await this.handleGenerateExplanation(message.codeContext);
                            break;
                        case 'copyCode':
                            // 处理复制代码请求
                            try {
                                await vscode.env.clipboard.writeText(message.text);
                                console.log('[WebviewManager] Code copied to clipboard');
                            } catch (error) {
                                console.error('[WebviewManager] Failed to copy code:', error);
                            }
                            break;
                        case 'close':
                            console.log('[WebviewManager] Closing webview panel');
                            this.currentPanel?.dispose();
                            break;
                        case 'debug':
                            // 静默处理调试消息，避免刷屏
                            break;
                        case 'echo':
                            // 测试消息通道（静默）
                            this.sendMessageToWebview({ type: 'echoResponse', data: message.data });
                            break;
                case 'openUrl':
                    if (message.url && typeof message.url === 'string') {
                        try {
                            // Hardcoded base URL for platform deep links (no user config required)
                            const baseUrl = 'http://localhost:3000';
                            const toAbs = (u: string): string => {
                                if (/^https?:\/\//i.test(u)) return u;
                                const prefix = baseUrl.replace(/\/$/, '');
                                const suffix = u.startsWith('/') ? u : `/${u}`;
                                return `${prefix}${suffix}`;
                            };
                            const absUrl = toAbs(message.url);
                            await vscode.env.openExternal(vscode.Uri.parse(absUrl));
                        } catch (err) {
                            console.error('[WebviewManager] Failed to open URL:', err);
                        }
                    }
                    break;
                }
                },
                null,
                this.context.subscriptions
            );

            // 设置 HTML 内容
            this.currentPanel.webview.html = this.getHtmlForWebview(this.currentPanel.webview);

            // 监听面板关闭事件
            this.currentPanel.onDidDispose(() => {
                console.log('[WebviewManager] Panel disposed, cancelling generation');
                this.cancelCurrentGeneration();
                this.currentPanel = undefined;
            }, null, this.context.subscriptions);
        }
    }

    private sendMessageToWebview(message: any) {
        if (this.currentPanel) {
            // 静默发送，避免在流式输出（generationChunk）时刷屏
            this.currentPanel.webview.postMessage(message);
        } else {
            console.log('[WebviewManager] Warning: No current panel to send message to');
        }
    }

    private async handleGenerateExplanation(codeContext: CodeContext) {
        const signal = this.currentAbortController?.signal;
        
        try {
            // ========== AST 分析开始 ==========
            console.log('\n========== AST 分析开始 ==========');
            console.log('代码片段:', codeContext.code.substring(0, 200) + (codeContext.code.length > 200 ? '...' : ''));
            console.log('语言:', codeContext.language);
            
            const analyzer = UnifiedAstAnalyzer.getInstance();
            const astResult = await analyzer.analyzeCode(codeContext.code, codeContext.language || 'javascript');
            
            // 详细日志输出
            console.log('\n📌 主要知识点:', astResult.aiContext.primaryTopic || '无');
            console.log('👤 用户水平:', astResult.aiContext.userLevel);
            
            console.log('\n🔍 提取的特征:');
            console.log('  语法特征:', astResult.aiContext.extractedFeatures.atomic.syntax.join(', '));
            console.log('  API调用:', astResult.aiContext.extractedFeatures.atomic.api.join(', '));
            console.log('  代码模式:', astResult.aiContext.extractedFeatures.structural.patterns.join(', '));
            console.log('  复杂度:', astResult.aiContext.extractedFeatures.structural.complexity);
            console.log('  嵌套深度:', astResult.aiContext.extractedFeatures.structural.nesting);
            
            console.log('\n📊 特征统计:');
            const stats = astResult.aiContext.extractedFeatures.statistical;
            console.log('  基础特征数:', stats.featureCount.basicCount);
            console.log('  中级特征数:', stats.featureCount.intermediateCount);
            console.log('  高级特征数:', stats.featureCount.advancedCount);
            
            console.log('\n📚 匹配的知识点:');
            astResult.knowledgeLinks.forEach((link, index) => {
                console.log(`  ${index + 1}. ${link.title} (相关度: ${link.relevance.toFixed(2)})`);
            });
            
            console.log('\n💬 AI 指导语:');
            console.log(astResult.aiContext.instruction);
            console.log('========== AST 分析结束 ==========\n');
            
            // Request knowledge links from web-learner
            try {
                // Hardcoded platform base URL for MVP; no VSCode setting required
                const baseUrl = 'http://localhost:3000';
                const endpoint = baseUrl.replace(/\/$/, '') + '/api/ast-match';
                const payload = {
                    features: astResult.aiContext.extractedFeatures,
                    language: (codeContext.language || 'javascript')
                };
                console.log('[WebviewManager] Requesting knowledge links from', endpoint);
                const resp = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (resp.ok) {
                    const data = await resp.json();
                    if (data && data.ok && Array.isArray(data.matches)) {
                        // Convert relative URLs from API (like "/learn?...") to absolute using baseUrl
                        const toAbs = (u: string): string => {
                            if (/^https?:\/\//i.test(u)) return u;
                            const prefix = baseUrl.replace(/\/$/, '');
                            const suffix = u.startsWith('/') ? u : `/${u}`;
                            return `${prefix}${suffix}`;
                        };
                        const links = data.matches.map((m: any) => ({ ...m, url: toAbs(m.url) }));
                        console.log(`[WebviewManager] ast-match ok: matches=${links.length}, primary=${data.primary || 'null'}`);
                        this.sendMessageToWebview({ type: 'knowledgeLinks', links });
                    } else {
                        console.warn('[WebviewManager] ast-match invalid payload or no matches');
                    }
                } else {
                    console.warn('[WebviewManager] ast-match response not ok:', resp.status);
                }
            } catch (err) {
                console.warn('[WebviewManager] Failed to fetch knowledge links:', err);
            }

            // 原有的 AI 服务流程
            const aiService = await AiServiceFactory.getService(this.context);
            
            // 发送开始生成的消息
            this.sendMessageToWebview({ 
                type: 'generationStarted',
                aiServiceName: aiService.getName()
            });

            // 流式生成并发送
            for await (const chunk of aiService.generateExplanation(codeContext, signal)) {
                // 检查是否被取消
                if (signal?.aborted) {
                    console.log('[WebviewManager] Generation cancelled during streaming');
                    break;
                }
                
                this.sendMessageToWebview({
                    type: 'generationChunk',
                    content: chunk
                });
            }

            // 只有在未取消的情况下发送完成消息
            if (!signal?.aborted) {
                this.sendMessageToWebview({ type: 'generationCompleted' });
            }
            
        } catch (error: any) {
            // 如果是取消错误，不发送错误消息
            if (error.message === 'Request aborted' || error.name === 'AbortError') {
                console.log('[WebviewManager] Generation cancelled');
                this.sendMessageToWebview({ 
                    type: 'generationCancelled',
                    message: '生成已取消'
                });
            } else {
                console.error('[WebviewManager] Error generating explanation:', error);
                this.sendMessageToWebview({ 
                    type: 'generationError',
                    error: error.message || '生成解释时发生错误'
                });
            }
        }
    }

    private cancelCurrentGeneration() {
        if (this.currentAbortController) {
            console.log('[WebviewManager] Cancelling current generation');
            this.currentAbortController.abort();
            this.currentAbortController = undefined;
        }
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        const scriptPath = path.join(this.context.extensionPath, 'dist', 'webview.js');
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.file(scriptPath)
        );

        const nonce = this.getNonce();

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none';
                    style-src ${webview.cspSource} 'unsafe-inline';
                    script-src ${webview.cspSource} 'nonce-${nonce}';
                        script-src-elem ${webview.cspSource} 'nonce-${nonce}';
                    font-src ${webview.cspSource};
                    img-src ${webview.cspSource} https:;">
                <title>AI 代码解释</title>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        height: 100vh;
                        overflow: auto;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: var(--vscode-foreground);
                        background: var(--vscode-editor-background);
                    }
                    #status {
                        padding: 10px;
                        margin: 10px 0;
                        background: var(--vscode-textBlockQuote-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: 4px;
                    }
                    .loading {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        color: var(--vscode-foreground);
                    }
                    .loading-spinner {
                        width: 20px;
                        height: 20px;
                        border: 2px solid var(--vscode-foreground);
                        border-top: 2px solid transparent;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <!-- 初始化脚本 -->
                <script nonce="${nonce}">
                    // 获取并共享 VSCode API
                    if (!window.vscode) {
                        window.vscode = window.acquireVsCodeApi ? window.acquireVsCodeApi() : null;
                    }
                    window.vsCodeApiReady = true;
                </script>
                
                <!-- React 应用容器 -->
                <div id="root">
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        <span>加载中...</span>
                    </div>
                </div>
                
                <!-- Process polyfill for WebView -->
                <script nonce="${nonce}">
                    if (typeof process === 'undefined') {
                        window.process = {
                            env: {
                                NODE_ENV: 'production'
                            }
                        };
                    }
                </script>
                
                <!-- 加载主脚本 -->
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }

    private getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}

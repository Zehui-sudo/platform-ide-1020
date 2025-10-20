import React, { useState, useEffect } from 'react';
import { MarkdownView } from './components/MarkdownView';

interface AppProps {
    vscode: any;
}

const App: React.FC<AppProps> = ({ vscode }) => {
    const [content, setContent] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [codeContext, setCodeContext] = useState<any>(null);
    const [aiServiceName, setAiServiceName] = useState<string>('Unknown');
    const [debugInfo, setDebugInfo] = useState<string[]>([]);
    const [showDebug, setShowDebug] = useState<boolean>(false); // 默认隐藏调试面板
    const [knowledgeLinks, setKnowledgeLinks] = useState<Array<{ title: string; url: string; score?: number; language?: string }>>([]);
    
    // 调试日志函数 - 同时发送到扩展主机
    const debugLog = (message: string, data?: any) => {
        const logMessage = data ? `${message}: ${JSON.stringify(data)}` : message;
        console.log(logMessage);
        
        // 发送到扩展主机
        vscode.postMessage({ 
            type: 'debug', 
            message: `[WebView → Extension] ${logMessage}` 
        });
        
        // 添加到调试信息显示
        setDebugInfo(prev => [...prev.slice(-20), `${new Date().toLocaleTimeString()}: ${logMessage}`]);
    };

    useEffect(() => {
        // 监听来自扩展的消息
        const handleMessage = async (event: MessageEvent) => {
            const message = event.data;
            debugLog('Received message', { type: message.type, codeLength: message.code?.length });
            
            switch (message.type) {
                case 'newExplanation':
                    debugLog('Received new code for explanation');
                    setCodeContext(message.codeContext);
                    setAiServiceName(message.aiServiceName || 'AI Service');
                    setContent('');
                    setIsLoading(true);
                    setDebugInfo([]); // 清空调试信息
                    
                    // 请求生成解释
                    vscode.postMessage({
                        type: 'generateExplanation',
                        codeContext: message.codeContext
                    });
                    break;
                    
                case 'generationStarted':
                    debugLog('AI generation started', { service: message.aiServiceName });
                    setAiServiceName(message.aiServiceName || 'AI Service');
                    setIsLoading(true);
                    break;
                    
                case 'generationChunk':
                    // 流式接收内容
                    setContent(prev => prev + message.content);
                    break;
                    
                case 'generationCompleted':
                    debugLog('AI generation completed');
                    setIsLoading(false);
                    break;
                    
                case 'generationError':
                    debugLog('AI generation error', message.error);
                    setContent(`## ❌ 生成解释时出错\n\n${message.error}`);
                    setIsLoading(false);
                    break;
                    
                case 'generationCancelled':
                    debugLog('AI generation cancelled');
                    // 不显示取消消息，保持当前内容
                    setIsLoading(false);
                    break;
                case 'knowledgeLinks':
                    debugLog('Received knowledge links');
                    if (Array.isArray(message.links)) {
                        setKnowledgeLinks(message.links);
                    }
                    break;
            }
        };

        window.addEventListener('message', handleMessage);
        
        // 延迟一点发送 ready 消息，确保 WebView 完全加载
        const timer = setTimeout(() => {
            debugLog('WebView initialized, sending ready message');
            vscode.postMessage({ type: 'ready' });
        }, 100);
        
        return () => {
            window.removeEventListener('message', handleMessage);
            clearTimeout(timer);
        };
    }, [vscode]);

    // ESC 键关闭 WebView
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                handleClose();
            }
        };
        
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    const handleClose = () => {
        vscode.postMessage({ type: 'close' });
    };

    return (
        <div style={{ 
            fontFamily: 'var(--vscode-font-family)',
            fontSize: 'var(--vscode-font-size)',
            color: 'var(--vscode-foreground)',
            padding: '20px',
            minHeight: '100vh',
            boxSizing: 'border-box'
        }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '20px',
                paddingBottom: '10px',
                borderBottom: '1px solid var(--vscode-panel-border)'
            }}>
                <h2 style={{ margin: 0 }}>🤖 AI 代码解释 ({aiServiceName})</h2>
                <button 
                    onClick={handleClose}
                    style={{
                        background: 'var(--vscode-button-background)',
                        color: 'var(--vscode-button-foreground)',
                        border: 'none',
                        padding: '6px 14px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '13px'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'var(--vscode-button-hoverBackground)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'var(--vscode-button-background)';
                    }}
                >
                    关闭 (ESC)
                </button>
            </div>

            {/* 调试信息面板 */}
            {showDebug && (
                <div style={{
                    background: 'var(--vscode-textBlockQuote-background)',
                    border: '1px solid var(--vscode-panel-border)',
                    borderRadius: '4px',
                    padding: '10px',
                    marginBottom: '20px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    maxHeight: '150px',
                    overflowY: 'auto'
                }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🔍 调试信息</div>
                    <div>状态: {isLoading ? '生成中...' : '就绪'}</div>
                    <div>AI 服务: {aiServiceName}</div>
                    <div>内容长度: {content.length} 字符</div>
                    {codeContext && (
                        <>
                            <div>代码语言: {codeContext.language}</div>
                            <div>代码长度: {codeContext.code?.length || 0} 字符</div>
                        </>
                    )}
                    <div style={{ marginTop: '10px' }}>
                        <button 
                            onClick={() => {
                                if (codeContext) {
                                    debugLog('Test: Resending generation request');
                                    vscode.postMessage({
                                        type: 'generateExplanation',
                                        codeContext
                                    });
                                }
                            }}
                            disabled={!codeContext || isLoading}
                            style={{
                                marginRight: '10px',
                                padding: '4px 8px',
                                fontSize: '11px',
                                cursor: (!codeContext || isLoading) ? 'not-allowed' : 'pointer',
                                opacity: (!codeContext || isLoading) ? 0.5 : 1
                            }}
                        >
                            重新生成
                        </button>
                        <button 
                            onClick={() => {
                                debugLog('Test: Sending echo request');
                                vscode.postMessage({ type: 'echo', data: 'test' });
                            }}
                            style={{
                                padding: '4px 8px',
                                fontSize: '11px',
                                cursor: 'pointer'
                            }}
                        >
                            测试消息通道
                        </button>
                    </div>
                    {debugInfo.length > 0 && (
                        <div style={{ marginTop: '10px', fontSize: '10px', opacity: 0.8 }}>
                            {debugInfo.map((info, i) => (
                                <div key={i}>{info}</div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {isLoading && content === '' && (
                <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    color: 'var(--vscode-descriptionForeground)' 
                }}>
                    <div style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid var(--vscode-progressBar-background)',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }}></div>
                    <span>正在生成解释...</span>
                </div>
            )}

            {content && (
                <div style={{ 
                    animation: 'fadeIn 0.3s ease-in'
                }}>
                    <MarkdownView content={content} />
                </div>
            )}

            {knowledgeLinks && knowledgeLinks.length > 0 && (
                <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--vscode-panel-border)' }}>
                    <div style={{ fontSize: '13px', marginBottom: '8px', color: 'var(--vscode-descriptionForeground)' }}>相关知识点</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {knowledgeLinks.map((link, idx) => (
                            <button key={idx}
                                onClick={() => vscode.postMessage({ type: 'openUrl', url: link.url })}
                                title={link.title}
                                style={{
                                    border: '1px solid var(--vscode-panel-border)',
                                    background: 'transparent',
                                    color: 'var(--vscode-textLink-foreground)',
                                    padding: '6px 10px',
                                    borderRadius: '14px',
                                    cursor: 'pointer',
                                    fontSize: '12px'
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--vscode-editor-hoverHighlightBackground)')}
                                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                            >
                                {link.title}
                                {typeof link.score === 'number' && (
                                    <span style={{ marginLeft: '6px', opacity: 0.7 }}>({Math.round(link.score * 100)}%)</span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            `}</style>
        </div>
    );
};

export default App;

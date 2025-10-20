import React, { useMemo, useState, useEffect } from 'react';
import Prism from 'prismjs';

// 导入 VS Code Dark+ 主题
import 'prism-themes/themes/prism-vsc-dark-plus.css';

// 导入常用语言支持
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-tsx';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-scss';
import 'prismjs/components/prism-less';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-swift';
import 'prismjs/components/prism-kotlin';
import 'prismjs/components/prism-dart';
import 'prismjs/components/prism-docker';

interface CodeBlockProps {
    language: string;
    code: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ language, code }) => {
    const [copyButtonText, setCopyButtonText] = useState('复制');
    const [isCopying, setIsCopying] = useState(false);
    
    // 处理语言别名
    const normalizedLanguage = useMemo(() => {
        const languageMap: { [key: string]: string } = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'yml': 'yaml',
            'sh': 'bash',
            'shell': 'bash',
            'dockerfile': 'docker',
            'c++': 'cpp',
            'c#': 'csharp',
            'objective-c': 'objectivec',
            'obj-c': 'objectivec',
        };
        
        const lang = language?.toLowerCase() || 'plaintext';
        return languageMap[lang] || lang;
    }, [language]);

    // 高亮代码
    const highlightedCode = useMemo(() => {
        try {
            // 获取语言语法，如果不存在则使用 plaintext
            let grammar = Prism.languages[normalizedLanguage];
            let actualLanguage = normalizedLanguage;
            
            // 如果语言不存在，尝试一些常见的备选
            if (!grammar) {
                const fallbacks: { [key: string]: string[] } = {
                    'javascript': ['js', 'jsx'],
                    'typescript': ['ts', 'tsx'],
                    'python': ['py'],
                    'cpp': ['c++', 'cxx'],
                    'csharp': ['cs', 'c#'],
                    'bash': ['sh', 'shell'],
                };
                
                // 查找可能的备选语言
                for (const [key, aliases] of Object.entries(fallbacks)) {
                    if (aliases.includes(normalizedLanguage) || key === normalizedLanguage) {
                        if (Prism.languages[key]) {
                            grammar = Prism.languages[key];
                            actualLanguage = key;
                            break;
                        }
                    }
                }
            }
            
            // 如果还是没有找到，使用 plaintext
            if (!grammar) {
                grammar = Prism.languages.plaintext || {};
                actualLanguage = 'plaintext';
            }
            
            return Prism.highlight(code, grammar, actualLanguage);
        } catch (error) {
            console.error('[CodeBlock] Code highlighting error:', error);
            // 如果高亮失败，返回转义后的代码
            return code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
    }, [code, normalizedLanguage]);

    // 移除 useEffect，因为我们使用 dangerouslySetInnerHTML 手动设置内容

    return (
        <div style={{
            marginTop: '1em',
            marginBottom: '1em',
            borderRadius: '6px',
            overflow: 'hidden',
            background: 'var(--vscode-textCodeBlock-background)',
            border: '1px solid var(--vscode-panel-border)'
        }}>
            <div style={{
                padding: '8px 12px',
                background: 'var(--vscode-titleBar-activeBackground)',
                borderBottom: '1px solid var(--vscode-panel-border)',
                fontSize: '12px',
                color: 'var(--vscode-titleBar-activeForeground)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <span>{normalizedLanguage}</span>
                <button
                    onClick={async () => {
                        if (isCopying) return;
                        
                        setIsCopying(true);
                        
                        // 使用 vscode.postMessage 发送复制请求
                        if ((window as any).vscode) {
                            (window as any).vscode.postMessage({
                                type: 'copyCode',
                                text: code
                            });
                            
                            // 显示复制成功
                            setCopyButtonText('已复制!');
                            
                            // 2秒后恢复
                            setTimeout(() => {
                                setCopyButtonText('复制');
                                setIsCopying(false);
                            }, 2000);
                        } else {
                            // 降级方案：尝试使用 navigator.clipboard
                            try {
                                await navigator.clipboard.writeText(code);
                                setCopyButtonText('已复制!');
                                setTimeout(() => {
                                    setCopyButtonText('复制');
                                    setIsCopying(false);
                                }, 2000);
                            } catch (err) {
                                console.error('复制失败:', err);
                                setCopyButtonText('复制失败');
                                setTimeout(() => {
                                    setCopyButtonText('复制');
                                    setIsCopying(false);
                                }, 2000);
                            }
                        }
                    }}
                    disabled={isCopying}
                    style={{
                        background: isCopying ? 'var(--vscode-button-background)' : 'transparent',
                        border: 'none',
                        color: 'var(--vscode-titleBar-activeForeground)',
                        cursor: isCopying ? 'default' : 'pointer',
                        padding: '2px 8px',
                        fontSize: '11px',
                        borderRadius: '3px',
                        opacity: isCopying ? 1 : 0.7,
                        transition: 'all 0.2s',
                        minWidth: '50px'
                    }}
                    onMouseEnter={(e) => {
                        if (!isCopying) {
                            e.currentTarget.style.opacity = '1';
                            e.currentTarget.style.background = 'var(--vscode-toolbar-hoverBackground)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (!isCopying) {
                            e.currentTarget.style.opacity = '0.7';
                            e.currentTarget.style.background = 'transparent';
                        }
                    }}
                    title={isCopying ? '' : '复制代码'}
                >
                    {copyButtonText}
                </button>
            </div>
            <pre className={`language-${normalizedLanguage}`} style={{
                margin: 0,
                padding: '12px',
                overflow: 'auto',
                fontSize: '13px',
                fontFamily: 'var(--vscode-editor-font-family)',
                lineHeight: '1.5',
                maxHeight: '600px',
                background: 'transparent'
            }}>
                <code 
                    className={`language-${normalizedLanguage}`}
                    dangerouslySetInnerHTML={{ __html: highlightedCode }}
                    style={{
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                        lineHeight: 'inherit',
                        background: 'transparent'
                    }}
                />
            </pre>
        </div>
    );
};
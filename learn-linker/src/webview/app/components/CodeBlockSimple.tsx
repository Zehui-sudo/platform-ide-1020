import React, { useMemo, useState } from 'react';
import Prism from 'prismjs';

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

interface CodeBlockProps {
    language: string;
    code: string;
}

// VS Code Dark+ 主题颜色
const tokenColors: { [key: string]: React.CSSProperties } = {
    'comment': { color: '#6A9955', fontStyle: 'italic' },
    'prolog': { color: '#6A9955', fontStyle: 'italic' },
    'doctype': { color: '#6A9955', fontStyle: 'italic' },
    'cdata': { color: '#6A9955', fontStyle: 'italic' },
    'punctuation': { color: '#D4D4D4' },
    'property': { color: '#9CDCFE' },
    'tag': { color: '#569CD6' },
    'constant': { color: '#9CDCFE' },
    'symbol': { color: '#9CDCFE' },
    'deleted': { color: '#9CDCFE' },
    'boolean': { color: '#569CD6' },
    'number': { color: '#B5CEA8' },
    'selector': { color: '#D7BA7D' },
    'attr-name': { color: '#9CDCFE' },
    'string': { color: '#CE9178' },
    'char': { color: '#CE9178' },
    'builtin': { color: '#4EC9B0' },
    'inserted': { color: '#CE9178' },
    'operator': { color: '#D4D4D4' },
    'entity': { color: '#D4D4D4' },
    'url': { color: '#4EC9B0', textDecoration: 'underline' },
    'variable': { color: '#9CDCFE' },
    'atrule': { color: '#C586C0' },
    'attr-value': { color: '#CE9178' },
    'function': { color: '#DCDCAA' },
    'class-name': { color: '#4EC9B0' },
    'keyword': { color: '#569CD6' },
    'regex': { color: '#D16969' },
    'important': { color: '#569CD6', fontWeight: 'bold' },
    'bold': { fontWeight: 'bold' },
    'italic': { fontStyle: 'italic' },
    'namespace': { opacity: 0.7 },
    'parameter': { color: '#9CDCFE' },
    'decorator': { color: '#DCDCAA' },
    'macro': { color: '#DCDCAA' },
    'lifetime': { color: '#569CD6' },
};

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

    // 获取高亮后的 HTML 并转换为 React 元素
    const highlightedElements = useMemo(() => {
        try {
            // 获取语言语法
            let grammar = Prism.languages[normalizedLanguage];
            let actualLanguage = normalizedLanguage;
            
            if (!grammar) {
                // 尝试备选语言
                const fallbacks: { [key: string]: string[] } = {
                    'javascript': ['js', 'jsx'],
                    'typescript': ['ts', 'tsx'],
                    'python': ['py'],
                    'cpp': ['c++', 'cxx'],
                    'csharp': ['cs', 'c#'],
                    'bash': ['sh', 'shell'],
                };
                
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
            
            if (!grammar) {
                // 如果没有找到语法，返回纯文本
                return <span style={{ color: '#D4D4D4' }}>{code}</span>;
            }
            
            // 获取高亮的 HTML 并直接应用内联样式
            let styledHtml = Prism.highlight(code, grammar, actualLanguage);
            
            // 为每个 token 添加内联样式
            Object.entries(tokenColors).forEach(([tokenClass, style]) => {
                const regex = new RegExp(`<span class="token ${tokenClass}">`, 'g');
                const styleStr = Object.entries(style)
                    .map(([k, v]) => {
                        const cssKey = k.replace(/([A-Z])/g, '-$1').toLowerCase();
                        return `${cssKey}: ${v}`;
                    })
                    .join('; ');
                styledHtml = styledHtml.replace(regex, `<span class="token ${tokenClass}" style="${styleStr}">`);
            });
            
            // 使用 dangerouslySetInnerHTML 渲染带有内联样式的 HTML
            return <div dangerouslySetInnerHTML={{ __html: styledHtml }} />;
        } catch (error) {
            console.error('[CodeBlock] Highlighting error:', error);
            return <span style={{ color: '#D4D4D4' }}>{code}</span>;
        }
    }, [code, normalizedLanguage]);

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
            <pre style={{
                margin: 0,
                padding: '12px',
                overflow: 'auto',
                fontSize: '13px',
                fontFamily: 'var(--vscode-editor-font-family)',
                lineHeight: '1.5',
                maxHeight: '600px',
                background: 'transparent'
            }}>
                <code style={{
                    fontFamily: 'inherit',
                    fontSize: 'inherit',
                    lineHeight: 'inherit',
                    background: 'transparent',
                    display: 'block',
                    color: '#D4D4D4'
                }}>
                    {highlightedElements}
                </code>
            </pre>
        </div>
    );
};
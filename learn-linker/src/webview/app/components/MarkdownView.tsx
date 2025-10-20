import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { CodeBlock } from './CodeBlockSimple';

interface MarkdownViewProps {
    content: string;
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content }) => {
    const remarkPlugins = useMemo(() => [remarkGfm, remarkMath], []);
    const rehypePlugins = useMemo(() => [rehypeKatex], []);

    return (
        <div className="markdown-body">
            <ReactMarkdown
                remarkPlugins={remarkPlugins}
                rehypePlugins={rehypePlugins}
                components={{
                    // 段落
                    p: ({ children }) => (
                        <p style={{ 
                            marginTop: '0.5em', 
                            marginBottom: '0.5em',
                            lineHeight: '1.6' 
                        }}>
                            {children}
                        </p>
                    ),
                    
                    // 代码块
                    code: ({ className, children, ...props }) => {
                        const match = /language-(\w+)/.exec(className || '');
                        const codeContent = String(children).replace(/\n$/, '');

                        // 代码块 - 使用 CodeBlock 组件进行语法高亮
                        if (match) {
                            return (
                                <CodeBlock 
                                    language={match[1]} 
                                    code={codeContent} 
                                />
                            );
                        }
                        
                        // 内联代码
                        return (
                            <code 
                                style={{
                                    background: 'var(--vscode-textCodeBlock-background)',
                                    color: 'var(--vscode-textPreformat-foreground)',
                                    padding: '2px 4px',
                                    borderRadius: '3px',
                                    fontSize: '0.9em',
                                    fontFamily: 'var(--vscode-editor-font-family)'
                                }}
                                {...props}
                            >
                                {children}
                            </code>
                        );
                    },
                    
                    // 标题
                    h1: ({ children }) => (
                        <h1 style={{ 
                            fontSize: '1.8em', 
                            fontWeight: '600',
                            marginTop: '1em',
                            marginBottom: '0.5em',
                            borderBottom: '1px solid var(--vscode-panel-border)',
                            paddingBottom: '0.3em'
                        }}>
                            {children}
                        </h1>
                    ),
                    h2: ({ children }) => (
                        <h2 style={{ 
                            fontSize: '1.5em', 
                            fontWeight: '600',
                            marginTop: '1em',
                            marginBottom: '0.5em'
                        }}>
                            {children}
                        </h2>
                    ),
                    h3: ({ children }) => (
                        <h3 style={{ 
                            fontSize: '1.2em', 
                            fontWeight: '600',
                            marginTop: '0.8em',
                            marginBottom: '0.4em'
                        }}>
                            {children}
                        </h3>
                    ),
                    
                    // 链接
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                color: 'var(--vscode-textLink-foreground)',
                                textDecoration: 'none'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.textDecoration = 'underline';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.textDecoration = 'none';
                            }}
                        >
                            {children}
                        </a>
                    ),
                    
                    // 表格
                    table: ({ children }) => (
                        <div style={{ 
                            overflowX: 'auto', 
                            marginTop: '1em', 
                            marginBottom: '1em' 
                        }}>
                            <table style={{
                                width: '100%',
                                borderCollapse: 'collapse',
                                fontSize: '0.9em'
                            }}>
                                {children}
                            </table>
                        </div>
                    ),
                    thead: ({ children }) => (
                        <thead style={{
                            background: 'var(--vscode-editor-background)',
                            borderBottom: '2px solid var(--vscode-panel-border)'
                        }}>
                            {children}
                        </thead>
                    ),
                    tr: ({ children }) => (
                        <tr style={{
                            borderBottom: '1px solid var(--vscode-panel-border)'
                        }}>
                            {children}
                        </tr>
                    ),
                    th: ({ children }) => (
                        <th style={{
                            textAlign: 'left',
                            padding: '8px',
                            fontWeight: '600'
                        }}>
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td style={{
                            padding: '8px'
                        }}>
                            {children}
                        </td>
                    ),
                    
                    // 引用
                    blockquote: ({ children }) => (
                        <blockquote style={{
                            margin: '1em 0',
                            padding: '0.5em 1em',
                            borderLeft: '4px solid var(--vscode-textBlockQuote-border)',
                            background: 'var(--vscode-textBlockQuote-background)',
                            fontStyle: 'italic'
                        }}>
                            {children}
                        </blockquote>
                    ),
                    
                    // 列表
                    ul: ({ children }) => (
                        <ul style={{
                            marginTop: '0.5em',
                            marginBottom: '0.5em',
                            paddingLeft: '2em',
                            lineHeight: '1.6'
                        }}>
                            {children}
                        </ul>
                    ),
                    ol: ({ children }) => (
                        <ol style={{
                            marginTop: '0.5em',
                            marginBottom: '0.5em',
                            paddingLeft: '2em',
                            lineHeight: '1.6'
                        }}>
                            {children}
                        </ol>
                    ),
                    li: ({ children }) => (
                        <li style={{
                            marginTop: '0.25em',
                            marginBottom: '0.25em'
                        }}>
                            {children}
                        </li>
                    ),
                    
                    // 分隔线
                    hr: () => (
                        <hr style={{
                            margin: '1.5em 0',
                            border: 'none',
                            borderTop: '1px solid var(--vscode-panel-border)'
                        }} />
                    ),
                    
                    // 强调
                    strong: ({ children }) => (
                        <strong style={{ fontWeight: '600' }}>
                            {children}
                        </strong>
                    ),
                    em: ({ children }) => (
                        <em style={{ fontStyle: 'italic' }}>
                            {children}
                        </em>
                    )
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};
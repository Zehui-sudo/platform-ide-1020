import { IAiService, AiServiceConfig, CodeContext } from './IAiService';

/**
 * DeepSeek API 提供商实现
 * 兼容 OpenAI API 格式
 */
export class DeepSeekProvider implements IAiService {
    private config: AiServiceConfig;
    private readonly defaultEndpoint = 'https://api.deepseek.com/v1/chat/completions';
    private readonly defaultModel = 'deepseek-chat';

    constructor(config: AiServiceConfig) {
        this.config = {
            ...config,
            apiEndpoint: config.apiEndpoint || this.defaultEndpoint,
            model: config.model || this.defaultModel,
            maxTokens: config.maxTokens || 2000,
            temperature: config.temperature || 0.7
        };
    }

    getName(): string {
        return 'DeepSeek';
    }

    async validateConfig(): Promise<boolean> {
        if (!this.config.apiKey) {
            console.error('[DeepSeek] API key is missing');
            return false;
        }

        try {
            // 发送一个简单的测试请求
            const response = await fetch(this.config.apiEndpoint!, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.config.model,
                    messages: [{ role: 'user', content: 'Hi' }],
                    max_tokens: 5
                })
            });

            return response.ok;
        } catch (error) {
            console.error('[DeepSeek] Config validation failed:', error);
            return false;
        }
    }

    async* generateExplanation(context: CodeContext, signal?: AbortSignal): AsyncGenerator<string> {
        const messages = this.buildMessages(context);
        
        try {
            const response = await fetch(this.config.apiEndpoint!, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.config.model,
                    messages,
                    stream: true,
                    temperature: this.config.temperature,
                    max_tokens: this.config.maxTokens
                }),
                signal // 传递 AbortSignal
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`API request failed: ${response.status} - ${error}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('Response body is not readable');
            }

            let buffer = '';
            
            while (true) {
                // 检查是否被取消
                if (signal?.aborted) {
                    reader.cancel();
                    throw new Error('Request aborted');
                }
                
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            return;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            const content = parsed.choices?.[0]?.delta?.content;
                            if (content) {
                                yield content;
                            }
                        } catch (e) {
                            // 忽略解析错误，继续处理下一行
                            console.warn('[DeepSeek] Failed to parse SSE data:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('[DeepSeek] Error in generateExplanation:', error);
            throw error;
        }
    }

    async getFullExplanation(context: CodeContext, signal?: AbortSignal): Promise<string> {
        const messages = this.buildMessages(context);

        try {
            const response = await fetch(this.config.apiEndpoint!, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.config.model,
                    messages,
                    stream: false,
                    temperature: this.config.temperature,
                    max_tokens: this.config.maxTokens
                }),
                signal // 传递 AbortSignal
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`API request failed: ${response.status} - ${error}`);
            }

            const data = await response.json();
            return data.choices?.[0]?.message?.content || '无法生成解释';
        } catch (error) {
            console.error('[DeepSeek] Error in getFullExplanation:', error);
            throw error;
        }
    }

    private buildMessages(context: CodeContext) {
        const systemPrompt = `你是一个专业的代码解释助手。请为用户提供清晰、准确的代码解释。
要求：
1. 解释代码的主要功能和作用
2. 分析关键的算法、数据结构或设计模式
3. 使用 Markdown 格式，支持代码高亮和数学公式
4. 语言简洁易懂，适合各层次开发者`;

        let userContent = `请解释以下 ${context.language} 代码：\n\n\`\`\`${context.language}\n${context.code}\n\`\`\``;

        // 添加上下文信息
        if (context.surroundingCode) {
            userContent += `\n\n代码上下文：`;
            if (context.surroundingCode.before) {
                userContent += `\n前文：\n\`\`\`${context.language}\n${context.surroundingCode.before}\n\`\`\``;
            }
            if (context.surroundingCode.after) {
                userContent += `\n后文：\n\`\`\`${context.language}\n${context.surroundingCode.after}\n\`\`\``;
            }
        }

        if (context.imports && context.imports.length > 0) {
            userContent += `\n\n文件导入语句：\n\`\`\`${context.language}\n${context.imports.join('\n')}\n\`\`\``;
        }

        return [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userContent }
        ];
    }
}
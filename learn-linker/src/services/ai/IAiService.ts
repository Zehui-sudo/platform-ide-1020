/**
 * AI 服务接口定义
 * 所有 AI 提供商都需要实现这个接口
 */

export interface AiMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export interface AiServiceConfig {
    apiKey: string;
    apiEndpoint?: string;
    model?: string;
    maxTokens?: number;
    temperature?: number;
}

export interface CodeContext {
    code: string;
    language: string;
    fileName?: string;
    surroundingCode?: {
        before: string;
        after: string;
    };
    imports?: string[];
}

export interface AiResponse {
    content: string;
    usage?: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
    };
    error?: string;
}

export interface IAiService {
    /**
     * 生成代码解释（流式输出）
     * @param context 代码上下文
     * @param signal 可选的 AbortSignal，用于取消请求
     */
    generateExplanation(context: CodeContext, signal?: AbortSignal): AsyncGenerator<string>;
    
    /**
     * 获取完整的代码解释（非流式）
     * @param context 代码上下文
     * @param signal 可选的 AbortSignal，用于取消请求
     */
    getFullExplanation(context: CodeContext, signal?: AbortSignal): Promise<string>;
    
    /**
     * 验证服务配置是否有效
     */
    validateConfig(): Promise<boolean>;
    
    /**
     * 获取服务名称
     */
    getName(): string;
}
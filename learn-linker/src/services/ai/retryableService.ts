import { IAiService, CodeContext } from './IAiService';

/**
 * 带重试机制的 AI 服务装饰器
 */
export class RetryableAiService implements IAiService {
    private service: IAiService;
    private maxRetries: number;
    private retryDelay: number;

    constructor(service: IAiService, maxRetries: number = 3, retryDelay: number = 1000) {
        this.service = service;
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;
    }

    getName(): string {
        return this.service.getName();
    }

    async validateConfig(): Promise<boolean> {
        return await this.service.validateConfig();
    }

    async* generateExplanation(context: CodeContext, signal?: AbortSignal): AsyncGenerator<string> {
        let lastError: Error | null = null;
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            // 检查是否被取消
            if (signal?.aborted) {
                throw new Error('Request aborted');
            }
            
            try {
                console.log(`[RetryableAiService] Attempt ${attempt} of ${this.maxRetries}`);
                
                // 尝试调用服务，传递 signal
                yield* this.service.generateExplanation(context, signal);
                return; // 成功则返回
                
            } catch (error: any) {
                lastError = error;
                console.error(`[RetryableAiService] Attempt ${attempt} failed:`, error.message);
                
                // 如果是主动取消，不应该重试
                if (error.message === 'Request aborted' || error.name === 'AbortError') {
                    throw error;
                }
                
                // 判断是否是可重试的错误
                if (!this.isRetryableError(error)) {
                    throw error;
                }
                
                // 如果还有重试机会，等待后继续
                if (attempt < this.maxRetries) {
                    await this.delay(this.retryDelay * attempt); // 指数退避
                }
            }
        }
        
        // 所有重试都失败
        throw new Error(`服务调用失败，已重试 ${this.maxRetries} 次: ${lastError?.message}`);
    }

    async getFullExplanation(context: CodeContext, signal?: AbortSignal): Promise<string> {
        let lastError: Error | null = null;
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            // 检查是否被取消
            if (signal?.aborted) {
                throw new Error('Request aborted');
            }
            
            try {
                console.log(`[RetryableAiService] Attempt ${attempt} of ${this.maxRetries}`);
                return await this.service.getFullExplanation(context, signal);
                
            } catch (error: any) {
                lastError = error;
                console.error(`[RetryableAiService] Attempt ${attempt} failed:`, error.message);
                
                // 如果是主动取消，不应该重试
                if (error.message === 'Request aborted' || error.name === 'AbortError') {
                    throw error;
                }
                
                // 判断是否是可重试的错误
                if (!this.isRetryableError(error)) {
                    throw error;
                }
                
                // 如果还有重试机会，等待后继续
                if (attempt < this.maxRetries) {
                    await this.delay(this.retryDelay * attempt); // 指数退避
                }
            }
        }
        
        throw new Error(`服务调用失败，已重试 ${this.maxRetries} 次: ${lastError?.message}`);
    }

    private isRetryableError(error: any): boolean {
        // 网络错误、超时、5xx 错误等可以重试
        if (error.message?.includes('network') || 
            error.message?.includes('timeout') ||
            error.message?.includes('ECONNREFUSED') ||
            error.message?.includes('ETIMEDOUT')) {
            return true;
        }
        
        // API 速率限制错误可以重试
        if (error.message?.includes('rate limit') ||
            error.message?.includes('429')) {
            return true;
        }
        
        // 5xx 服务器错误可以重试
        if (error.message?.includes('500') ||
            error.message?.includes('502') ||
            error.message?.includes('503') ||
            error.message?.includes('504')) {
            return true;
        }
        
        // 4xx 客户端错误不应重试（除了 429）
        if (error.message?.includes('401') ||
            error.message?.includes('403') ||
            error.message?.includes('404')) {
            return false;
        }
        
        return false;
    }

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
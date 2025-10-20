import * as vscode from 'vscode';
import { IAiService, AiServiceConfig } from './IAiService';
import { DeepSeekProvider } from './deepseekProvider';
import { MockAiService } from '../mockAiService';
import { RetryableAiService } from './retryableService';

/**
 * AI 服务工厂类
 * 负责根据配置创建相应的 AI 服务实例
 */
export class AiServiceFactory {
    private static instance: IAiService | null = null;

    /**
     * 获取 AI 服务实例
     */
    static async getService(context: vscode.ExtensionContext): Promise<IAiService> {
        // 如果已有实例且配置未变，直接返回
        if (this.instance && !this.isConfigChanged()) {
            return this.instance;
        }

        const config = vscode.workspace.getConfiguration('learnLinker');
        const provider = config.get<string>('aiProvider', 'mock');

        console.log(`[AiServiceFactory] Creating AI service for provider: ${provider}`);

        switch (provider) {
            case 'deepseek':
                this.instance = await this.createDeepSeekService(context);
                break;
            case 'mock':
            default:
                this.instance = new MockAiService();
                break;
        }

        return this.instance;
    }

    /**
     * 创建 DeepSeek 服务
     */
    private static async createDeepSeekService(context: vscode.ExtensionContext): Promise<IAiService> {
        const config = vscode.workspace.getConfiguration('learnLinker');
        
        // 尝试从配置获取 API Key
        let apiKey = config.get<string>('deepseekApiKey', '');
        
        // 如果配置中没有，尝试从 SecretStorage 获取
        if (!apiKey) {
            apiKey = await context.secrets.get('learnLinker.deepseekApiKey') || '';
        }
        
        // 如果还是没有，提示用户输入
        if (!apiKey) {
            apiKey = await this.promptForApiKey(context) || '';
        }
        
        if (!apiKey) {
            vscode.window.showWarningMessage('DeepSeek API Key 未配置，将使用模拟服务');
            return new MockAiService();
        }

        const serviceConfig: AiServiceConfig = {
            apiKey,
            model: config.get<string>('aiModel', 'deepseek-chat'),
            maxTokens: config.get<number>('maxTokens', 2000),
            temperature: config.get<number>('temperature', 0.7),
            apiEndpoint: config.get<string>('deepseekApiEndpoint')
        };

        let service: IAiService = new DeepSeekProvider(serviceConfig);
        
        // 验证配置
        const isValid = await service.validateConfig();
        if (!isValid) {
            vscode.window.showErrorMessage('DeepSeek API 配置无效，请检查 API Key');
            return new MockAiService();
        }

        // 包装重试机制
        service = new RetryableAiService(service, 3, 1000);

        vscode.window.showInformationMessage(`已启用 ${service.getName()} AI 服务`);
        return service;
    }

    /**
     * 提示用户输入 API Key
     */
    private static async promptForApiKey(context: vscode.ExtensionContext): Promise<string | undefined> {
        const result = await vscode.window.showInformationMessage(
            '需要配置 DeepSeek API Key 才能使用 AI 解释功能',
            '立即配置',
            '稍后'
        );

        if (result === '立即配置') {
            const apiKey = await vscode.window.showInputBox({
                prompt: '请输入 DeepSeek API Key',
                placeHolder: 'sk-...',
                password: true,
                ignoreFocusOut: true,
                validateInput: (value) => {
                    if (!value) {
                        return 'API Key 不能为空';
                    }
                    if (!value.startsWith('sk-')) {
                        return 'API Key 格式不正确';
                    }
                    return null;
                }
            });

            if (apiKey) {
                // 安全存储 API Key
                await context.secrets.store('learnLinker.deepseekApiKey', apiKey);
                vscode.window.showInformationMessage('API Key 已安全保存');
                return apiKey;
            }
        }

        return undefined;
    }

    /**
     * 检查配置是否已更改
     */
    private static isConfigChanged(): boolean {
        // 这里可以实现更复杂的配置变化检测逻辑
        // 目前简化处理，总是返回 false
        return false;
    }

    /**
     * 清除缓存的实例
     */
    static clearInstance(): void {
        this.instance = null;
    }
}
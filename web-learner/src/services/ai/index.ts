import { getChatLLMConfig, isChatLLMConfigured } from '@/server/config/chatLLM';
import { AIProvider, AIProviderType } from './types';
import { OpenAIProvider, type OpenAIProviderOptions } from './providers/openai';
import { DeepSeekProvider } from './providers/deepseek';
import { GeminiProvider, type GeminiProviderOptions } from './providers/gemini';

export * from './types';

export function createAIProvider(type: AIProviderType): AIProvider {
  const chatConfig = getChatLLMConfig(type);

  switch (type) {
    case 'openai':
      return new OpenAIProvider(
        chatConfig
          ? buildOpenAIOptions(chatConfig.config)
          : undefined
      );
    case 'deepseek':
      return new DeepSeekProvider(
        chatConfig
          ? buildOpenAIOptions(chatConfig.config)
          : undefined
      );
    case 'gemini':
      return new GeminiProvider(
        chatConfig
          ? buildGeminiOptions(chatConfig.config)
          : undefined
      );
    default:
      throw new Error(`Unknown AI provider: ${type}`);
  }
}

export function getAvailableProviders(): AIProviderType[] {
  const providers: AIProviderType[] = [];

  if (process.env.OPENAI_API_KEY || isChatLLMConfigured('openai')) providers.push('openai');
  if (process.env.DEEPSEEK_API_KEY || isChatLLMConfigured('deepseek')) providers.push('deepseek');
  if (process.env.GEMINI_API_KEY || isChatLLMConfigured('gemini')) providers.push('gemini');

  return providers;
}

const buildOpenAIOptions = (config: {
  apiKey?: string;
  apiBase?: string;
  model?: string;
  fallbackModel?: string | null;
}): OpenAIProviderOptions => {
  const options: OpenAIProviderOptions = {};

  if (config.apiKey) {
    options.apiKey = config.apiKey;
  }
  if (config.apiBase) {
    options.apiBase = config.apiBase;
  }
  if (config.model) {
    options.model = config.model;
  }
  if (config.fallbackModel !== undefined) {
    options.fallbackModel = config.fallbackModel;
  }

  return options;
};

const buildGeminiOptions = (config: {
  apiKey?: string;
  apiBase?: string;
  model?: string;
}): GeminiProviderOptions => {
  const options: GeminiProviderOptions = {};

  if (config.apiKey) {
    options.apiKey = config.apiKey;
  }
  if (config.apiBase) {
    options.apiBase = config.apiBase;
  }
  if (config.model) {
    options.model = config.model;
  }

  return options;
};

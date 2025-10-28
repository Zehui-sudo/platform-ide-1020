import { AIProvider, AIProviderType } from './types';
import { OpenAIProvider } from './providers/openai';
import { DeepSeekProvider } from './providers/deepseek';
import { GeminiProvider } from './providers/gemini';

export * from './types';

export function createAIProvider(type: AIProviderType): AIProvider {
  switch (type) {
    case 'openai':
      return new OpenAIProvider();
    case 'deepseek':
      return new DeepSeekProvider();
    case 'gemini':
      return new GeminiProvider();
    default:
      throw new Error(`Unknown AI provider: ${type}`);
  }
}

export function getAvailableProviders(): AIProviderType[] {
  const providers: AIProviderType[] = [];
  
  if (process.env.OPENAI_API_KEY) providers.push('openai');
  if (process.env.DEEPSEEK_API_KEY) providers.push('deepseek');
  if (process.env.GEMINI_API_KEY) providers.push('gemini');
  
  return providers;
}

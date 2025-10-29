import { OpenAIProvider, type OpenAIProviderOptions } from './openai';
import { ChatRequest, ChatResponse } from '../types';

const normalizeDeepSeekBase = (base?: string): string => {
  const fallback = 'https://api.deepseek.com/v1';
  if (!base) return fallback;
  const trimmed = base.replace(/\/+$/, '');
  if (trimmed.endsWith('/v1')) return trimmed;
  return `${trimmed}/v1`;
};

export class DeepSeekProvider extends OpenAIProvider {
  constructor(options: OpenAIProviderOptions = {}) {
    super({
      apiKey: options.apiKey ?? process.env.DEEPSEEK_API_KEY ?? '',
      model: options.model ?? process.env.DEEPSEEK_MODEL ?? 'deepseek-chat',
      apiBase: normalizeDeepSeekBase(options.apiBase ?? process.env.DEEPSEEK_API_BASE),
      fallbackModel: options.fallbackModel ?? null,
    });
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  async chat(request: ChatRequest): Promise<ChatResponse | ReadableStream> {
    // DeepSeek uses OpenAI-compatible API, so we can call the parent method
    const response = await super.chat(request);

    // If the response is a stream, we don't need to modify it.
    if (response instanceof ReadableStream) {
      return response;
    }

    // If it's a regular response, update the provider field.
    return {
      ...response,
      provider: 'deepseek',
    };
  }
}

import { AIProvider, ChatRequest, ChatResponse } from '../types';
import { ChatMessage } from '@/types';

export class OpenAIProvider extends AIProvider {
  protected apiKey: string;
  protected model: string;
  protected apiBase: string;

  constructor() {
    super();
    this.apiKey = process.env.OPENAI_API_KEY || '';
    this.model = process.env.OPENAI_MODEL || 'gpt-3.5-turbo';
    this.apiBase = process.env.OPENAI_API_BASE || 'https://api.openai.com/v1';
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  getDefaultModel(): string {
    return this.model;
  }

  private formatMessages(messages: ChatMessage[]) {
    const processedMessages = [...messages];

    // If the first message is from the AI and there are subsequent messages, remove it.
    // Most chat APIs require the conversation to start with a user message.
    if (processedMessages.length > 1 && processedMessages[0].sender === 'ai') {
      processedMessages.shift(); // Removes the initial AI greeting
    }

    return processedMessages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.content,
    }));
  }

  private _createParserStream(stream: ReadableStream): ReadableStream {
    const decoder = new TextDecoder();
    const transformStream = new TransformStream({
      async transform(chunk, controller) {
        const text = decoder.decode(chunk, { stream: true });
        const lines = text.split('\n').filter(line => line.trim().startsWith('data:'));
        
        for (const line of lines) {
          const jsonStr = line.replace(/^data: /, '');
          if (jsonStr === '[DONE]') {
            controller.terminate();
            return;
          }
          try {
            const parsed = JSON.parse(jsonStr);
            const delta = parsed.choices[0]?.delta?.content;
            if (delta) {
              controller.enqueue(new TextEncoder().encode(delta));
            }
          } catch {
            console.error('Failed to parse stream chunk in provider:', jsonStr);
          }
        }
      }
    });

    return stream.pipeThrough(transformStream);
  }

  async chat(request: ChatRequest): Promise<ChatResponse | ReadableStream> {
    if (!this.isConfigured()) {
      throw new Error('OpenAI API key not configured');
    }

    const { messages, model = this.model, temperature = 0.7, maxTokens = 2000, contextReference, stream = false, language } = request;

    // Add context if provided
    let formattedMessages = this.formatMessages(messages);
    if (contextReference) {
      const sourceText = contextReference.source ? `的[${contextReference.source}]这一章节` : '';
      const languageText = language ? `的[${language}]` : '';

      const progressText = (typeof contextReference.progressPercent === 'number')
        ? `，目前已阅读约${contextReference.progressPercent}%`
        : '';
      const readSoFarText = contextReference.readSoFar
        ? `\n\n【已阅读内容节选】\n${contextReference.readSoFar}`
        : '';

      const contextMessage = {
        role: 'system' as const,
        content:
          `你是一个AI学习助手。用户现在正在学习${languageText}${sourceText}的知识点${progressText}。` +
          `${readSoFarText}\n\n` +
          `【用户勾选内容】\n${contextReference.text}\n\n` +
          `请结合用户的阅读进度与勾选内容进行解释，回答需要自然、友好、易于理解。`
      };
      // Dev prompt logging (printed by Next dev server / Edge runtime logs)
      try {
        console.log('[AI Prompt] Provider=openai-compatible model=%s', model);
        console.log(contextMessage.content);
      } catch {}
      formattedMessages = [contextMessage, ...formattedMessages];
    }
    else {
      try {
        console.log('[AI Prompt] Provider=openai-compatible model=%s (no system context)', model);
        const lastUser = [...messages].reverse().find(m => m.sender === 'user');
        if (lastUser?.content) console.log('Last user message:\n' + lastUser.content);
      } catch {}
    }

    try {
      const response = await fetch(`${this.apiBase}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages: formattedMessages,
          temperature,
          max_tokens: maxTokens,
          stream,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || `OpenAI API error: ${response.status}`);
      }

      if (stream) {
        if (!response.body) {
          throw new Error('Response body is null for streaming request');
        }
        return this._createParserStream(response.body);
      }

      const data = await response.json();
      
      return {
        content: data.choices[0].message.content,
        provider: 'openai',
        model,
        usage: data.usage ? {
          promptTokens: data.usage.prompt_tokens,
          completionTokens: data.usage.completion_tokens,
          totalTokens: data.usage.total_tokens,
        } : undefined,
      };
    } catch (error) {
      console.error('OpenAI API error:', error);
      throw error;
    }
  }
}

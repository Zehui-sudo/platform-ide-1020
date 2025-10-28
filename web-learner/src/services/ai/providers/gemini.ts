import { AIProvider, ChatRequest, ChatResponse } from '../types';
import { ChatMessage } from '@/types';

type GeminiContentPart = { text: string };
type GeminiContent = { role: 'user' | 'model'; parts: GeminiContentPart[] };

export class GeminiProvider extends AIProvider {
  private readonly apiKey: string;
  private readonly model: string;
  private readonly apiBase: string;

  constructor() {
    super();
    this.apiKey = process.env.GEMINI_API_KEY || '';
    this.model = process.env.GEMINI_MODEL || 'gemini-1.5-pro-latest';
    this.apiBase = process.env.GEMINI_API_BASE || 'https://generativelanguage.googleapis.com/v1beta';
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  getDefaultModel(): string {
    return this.model;
  }

  private formatMessages(messages: ChatMessage[]): GeminiContent[] {
    const formatted: GeminiContent[] = [];

    for (const message of messages) {
      if (!message.content?.trim()) continue;

      formatted.push({
        role: message.sender === 'user' ? 'user' : 'model',
        parts: [{ text: message.content }],
      });
    }

    return formatted;
  }

  private buildSystemInstruction(request: ChatRequest): GeminiContent | undefined {
    const { contextReference, language } = request;
    if (!contextReference) return undefined;

    const sourceText = contextReference.source ? `的[${contextReference.source}]这一章节` : '';
    const languageText = language ? `的[${language}]` : '';
    const progressText =
      typeof contextReference.progressPercent === 'number'
        ? `，目前已阅读约${contextReference.progressPercent}%`
        : '';
    const readSoFarText = contextReference.readSoFar
      ? `\n\n【已阅读内容节选】\n${contextReference.readSoFar}`
      : '';

    return {
      role: 'user',
      parts: [
        {
          text:
            `你是一个AI学习助手。用户正在学习${languageText}${sourceText}的知识点${progressText}。\n\n` +
            `【用户勾选内容】\n${contextReference.text}${readSoFarText}\n\n` +
            `请结合用户的阅读进度与勾选内容进行解释，回答需要自然、友好、易于理解。`,
        },
      ],
    };
  }

  private async streamResponse(response: Response): Promise<ReadableStream> {
    if (!response.body) {
      throw new Error('Response body is null for streaming request');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const encoder = new TextEncoder();

    return new ReadableStream({
      async start(controller) {
        let buffer = '';
        const dataPrefix = 'data:';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            let eolIndex;
            while ((eolIndex = buffer.indexOf('\n')) >= 0) {
              const line = buffer.slice(0, eolIndex).trim();
              buffer = buffer.slice(eolIndex + 1);

              if (line.startsWith(dataPrefix)) {
                const jsonStr = line.slice(dataPrefix.length).trim();
                if (jsonStr === '[DONE]' || !jsonStr) {
                  continue;
                }
                try {
                  const parsed = JSON.parse(jsonStr);
                  const candidate = parsed?.candidates?.[0];
                  const parts: GeminiContentPart[] | undefined = candidate?.content?.parts;
                  if (!parts?.length) continue;

                  const text = parts
                    .map((part: GeminiContentPart) => part.text ?? '')
                    .filter(Boolean)
                    .join('');

                  if (text) {
                    controller.enqueue(encoder.encode(text));
                  }
                } catch (error) {
                  console.error('Failed to parse Gemini stream chunk:', jsonStr, error);
                }
              }
            }
          }
          controller.close();
        } catch (error) {
          controller.error(error);
        }
      },
      cancel() {
        reader.cancel().catch(() => {});
      },
    });
  }

  async chat(request: ChatRequest): Promise<ChatResponse | ReadableStream> {
    if (!this.isConfigured()) {
      throw new Error('Gemini API key not configured');
    }

    const {
      messages,
      model = this.model,
      temperature = 0.7,
      maxTokens = 2048,
      contextReference,
      stream = false,
      language,
    } = request;

    const formattedMessages = this.formatMessages(messages);
    const systemInstruction = this.buildSystemInstruction({
      ...request,
      contextReference,
      language,
    });

    const payload: Record<string, unknown> = {
      contents: formattedMessages,
      generationConfig: {
        temperature,
        maxOutputTokens: maxTokens,
      },
    };

    if (systemInstruction) {
      payload.systemInstruction = systemInstruction;
    }

    const endpoint = stream ? 'streamGenerateContent' : 'generateContent';
    const url = `${this.apiBase}/models/${model}:${endpoint}?key=${this.apiKey}${
      stream ? '&alt=sse' : ''
    }`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error?.message || `Gemini API error: ${response.status}`);
      }

      if (stream) {
        return this.streamResponse(response);
      }

      const data = await response.json();
      const candidate = data.candidates?.[0];
      const text = candidate?.content?.parts
        ?.map((part: GeminiContentPart) => part.text ?? '')
        .join('');

      return {
        content: text || '',
        provider: 'gemini',
        model,
      };
    } catch (error) {
      console.error('Gemini API error:', error);
      throw error;
    }
  }
}

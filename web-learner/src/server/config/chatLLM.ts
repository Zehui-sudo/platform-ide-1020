import fs from 'fs';
import path from 'path';
import type { AIProviderType } from '@/types';

type RawLLMEntry = Record<string, unknown>;

export interface NormalizedLLMConfig {
  provider?: string;
  apiKey?: string;
  apiBase?: string;
  model?: string;
  fallbackModel?: string | null;
  temperature?: number;
  raw: RawLLMEntry;
}

interface AppConfig {
  llms?: Record<string, RawLLMEntry | undefined>;
  chat_llm?: Record<string, unknown>;
}

export interface ChatLLMSelection {
  key: string;
  config: NormalizedLLMConfig;
}

let cachedConfig: AppConfig | null = null;
let configLoaded = false;
const selectionCache = new Map<AIProviderType, ChatLLMSelection | null>();

const candidateConfigPaths = (): string[] => {
  const cwd = process.cwd();
  const paths: Array<string | undefined> = [
    process.env.APP_CONFIG_PATH,
    path.join(cwd, 'config.json'),
    path.join(cwd, '..', 'config.json'),
  ];
  return paths
    .filter((p): p is string => !!p)
    .map((p) => path.resolve(p));
};

const locateConfigPath = (): string | null => {
  for (const candidate of candidateConfigPaths()) {
    try {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
    } catch {
      // ignore errors from existsSync (e.g., permission issues) and continue
    }
  }
  return null;
};

const loadConfig = (): AppConfig => {
  if (configLoaded && cachedConfig) {
    return cachedConfig;
  }
  configLoaded = true;

  const configPath = locateConfigPath();
  if (!configPath) {
    cachedConfig = {};
    return cachedConfig;
  }

  try {
    const content = fs.readFileSync(configPath, 'utf8');
    cachedConfig = JSON.parse(content) as AppConfig;
  } catch (error) {
    console.error('[chatLLM] Failed to read config.json:', error);
    cachedConfig = {};
  }
  return cachedConfig;
};

const toStringOrUndefined = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : undefined;
  }
  return undefined;
};

const normalizeLLMEntry = (entry: RawLLMEntry, key: string): NormalizedLLMConfig => {
  const apiKey =
    toStringOrUndefined(entry['api_key']) ??
    toStringOrUndefined(entry['apiKey']) ??
    toStringOrUndefined(entry['token']);
  const apiBase =
    toStringOrUndefined(entry['api_base']) ??
    toStringOrUndefined(entry['base_url']) ??
    toStringOrUndefined(entry['baseUrl']) ??
    toStringOrUndefined(entry['endpoint']);
  const model = toStringOrUndefined(entry['model']);

  const fallbackValue = entry['fallback_model'] ?? entry['fallbackModel'];
  let fallbackModel: string | null | undefined;
  if (typeof fallbackValue === 'string') {
    const trimmed = fallbackValue.trim();
    fallbackModel = trimmed.length > 0 ? trimmed : undefined;
  } else if (fallbackValue === null) {
    fallbackModel = null;
  }

  const temperature =
    typeof entry['temperature'] === 'number' ? (entry['temperature'] as number) : undefined;
  const provider = toStringOrUndefined(entry['provider']);

  return {
    provider,
    apiKey,
    apiBase,
    model,
    fallbackModel,
    temperature,
    raw: { ...entry, key },
  };
};

const pickMappingKey = (
  mapping: Record<string, unknown>,
  provider: AIProviderType
): string | undefined => {
  const providerKey = provider.toLowerCase();
  const direct = mapping[providerKey] ?? mapping[provider];

  if (typeof direct === 'string') {
    return direct;
  }

  if (direct && typeof direct === 'object') {
    const nestedDefault = (direct as Record<string, unknown>).default;
    if (typeof nestedDefault === 'string') {
      return nestedDefault;
    }
  }

  const defaultKey = mapping.default;
  return typeof defaultKey === 'string' ? defaultKey : undefined;
};

export const getChatLLMConfig = (provider: AIProviderType): ChatLLMSelection | null => {
  if (selectionCache.has(provider)) {
    return selectionCache.get(provider) ?? null;
  }

  const cfg = loadConfig();
  const mapping = cfg.chat_llm;
  const llms = cfg.llms;

  if (!mapping || !llms) {
    selectionCache.set(provider, null);
    return null;
  }

  const key = pickMappingKey(mapping, provider);
  if (!key) {
    selectionCache.set(provider, null);
    return null;
  }

  const entry = llms[key];
  if (!entry) {
    console.warn(`[chatLLM] chat_llm entry "${key}" not found in llms registry`);
    selectionCache.set(provider, null);
    return null;
  }

  const normalized = normalizeLLMEntry(entry, key);
  const result: ChatLLMSelection = {
    key,
    config: normalized,
  };
  selectionCache.set(provider, result);
  return result;
};

export const isChatLLMConfigured = (provider: AIProviderType): boolean => {
  return getChatLLMConfig(provider) !== null;
};

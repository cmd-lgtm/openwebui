import { ModelConfig } from '../types/ai.types';

export const AI_MODELS: ModelConfig[] = [
  // OpenAI
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai', maxTokens: 4096, contextWindow: 128000, costPer1kInput: 0.005, costPer1kOutput: 0.015 },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai', maxTokens: 16384, contextWindow: 128000, costPer1kInput: 0.00015, costPer1kOutput: 0.0006 },
  { id: 'o1', name: 'o1', provider: 'openai', maxTokens: 32768, contextWindow: 200000, costPer1kInput: 0.015, costPer1kOutput: 0.06 },

  // Anthropic
  { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'anthropic', maxTokens: 8192, contextWindow: 200000, costPer1kInput: 0.003, costPer1kOutput: 0.015 },
  { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', provider: 'anthropic', maxTokens: 8192, contextWindow: 200000, costPer1kInput: 0.001, costPer1kOutput: 0.005 },

  // Google
  { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'google', maxTokens: 8192, contextWindow: 1000000, costPer1kInput: 0.00125, costPer1kOutput: 0.005 },
  { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', provider: 'google', maxTokens: 8192, contextWindow: 1000000, costPer1kInput: 0.0001, costPer1kOutput: 0.0004 },

  // DeepSeek
  { id: 'deepseek-chat', name: 'DeepSeek V3', provider: 'deepseek', maxTokens: 8192, contextWindow: 128000, costPer1kInput: 0.00014, costPer1kOutput: 0.00028 },
  { id: 'deepseek-reasoner', name: 'DeepSeek R1', provider: 'deepseek', maxTokens: 8192, contextWindow: 128000, costPer1kInput: 0.00055, costPer1kOutput: 0.0022 },

  // Groq
  { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', provider: 'groq', maxTokens: 4096, contextWindow: 128000, costPer1kInput: 0.00059, costPer1kOutput: 0.00079 },
];

export const DEFAULT_MODEL = AI_MODELS.find(m => m.id === 'claude-sonnet-4-20250514')!;

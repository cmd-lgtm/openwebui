// ===== AI Types =====

export type ProviderType =
  | 'openai'
  | 'anthropic'
  | 'google'
  | 'deepseek'
  | 'groq'
  | 'mistral'
  | 'openrouter'
  | 'cohere'
  | 'xai'
  | 'azure-openai'
  | 'aws-bedrock'
  | 'ollama'
  | 'lmstudio'
  | 'llamacpp'
  | 'vllm'
  | 'localai'
  | 'jan'
  | 'koboldcpp';

export interface ModelConfig {
  id: string;
  name: string;
  provider: ProviderType;
  maxTokens: number;
  contextWindow: number;
  isLocal?: boolean;
  size?: number;
  parameterSize?: string;
  quantization?: string;
  costPer1kInput?: number;
  costPer1kOutput?: number;
}

export interface AIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface AIRequest {
  model: ModelConfig;
  messages: AIMessage[];
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  stop?: string[];
  skipCache?: boolean;
  context?: Record<string, unknown>;
}

export interface AIResponse {
  content: string;
  model: string;
  provider: string;
  usage: TokenUsage;
  latency: number;
  finishReason: 'stop' | 'length' | 'error';
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface AIStreamChunk {
  content: string;
  done: boolean;
}

export type AIStreamCallback = (chunk: AIStreamChunk) => void;

export interface CostReport {
  totalCost: number;
  byProvider: Record<string, number>;
  byModel: Record<string, { cost: number; tokens: number; requests: number }>;
}

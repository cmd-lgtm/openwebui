// ===== Agent Types =====

import { ProviderType } from './ai.types';

export interface AgentConfig {
  id: string;
  name: string;
  role: AgentRole;
  description: string;
  systemPrompt: string;
  model: { id: string; provider: ProviderType };
  tools: string[];
  temperature?: number;
  maxTokens?: number;
}

export type AgentRole =
  | 'architect'
  | 'coder'
  | 'reviewer'
  | 'debugger'
  | 'tester'
  | 'refactor'
  | 'docs'
  | 'security'
  | 'devops'
  | 'database'
  | 'ui'
  | 'performance'
  | 'api'
  | 'terminal'
  | 'research';

export type AgentStatus = 'idle' | 'working' | 'error' | 'paused';

export interface Agent extends AgentConfig {
  status: AgentStatus;
  createdAt: Date;
  taskHistory: CompletedTask[];
  memory: AgentMemory[];
}

export interface AgentTask {
  id: string;
  description: string;
  context?: Record<string, unknown>;
  files?: Array<{ path: string; content: string }>;
  priority: 'low' | 'normal' | 'high' | 'critical';
}

export interface CompletedTask extends AgentTask {
  result: string;
  completedAt: Date;
}

export interface AgentMemory {
  task: string;
  result: string;
  timestamp: Date;
  content?: string;
}

export interface AgentMessage {
  content: string;
  context?: Record<string, unknown>;
  priority?: 'low' | 'normal' | 'high';
}

export type WorkflowType = 'sequential' | 'parallel' | 'hierarchical' | 'consensus' | 'debate' | 'swarm';

export interface WorkflowStep {
  id: string;
  agentId: string;
  instruction: string;
  context?: Record<string, unknown>;
  dependsOn?: string[];
  priority?: 'low' | 'normal' | 'high' | 'critical';
}

export interface AgentWorkflow {
  id: string;
  name: string;
  description: string;
  type: WorkflowType;
  steps: WorkflowStep[];
}

export interface WorkflowResult {
  workflowId: string;
  results: Record<string, string>;
  status: 'completed' | 'failed' | 'cancelled';
}

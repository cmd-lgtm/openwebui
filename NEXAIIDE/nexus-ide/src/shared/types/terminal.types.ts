// ===== Terminal Types =====

export interface TerminalOptions {
  shell?: string;
  cwd?: string;
  env?: Record<string, string>;
  cols?: number;
  rows?: number;
}

export interface TerminalInstance {
  id: string;
  shell: string;
  cwd: string;
  title: string;
  createdAt: Date;
  isActive: boolean;
}

export interface ShellInfo {
  name: string;
  path: string;
}

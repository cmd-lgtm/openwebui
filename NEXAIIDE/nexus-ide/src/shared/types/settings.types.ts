// ===== Settings Types =====

import { EditorSettings } from './editor.types';

export interface AppSettings {
  general: GeneralSettings;
  editor: EditorSettings;
  terminal: TerminalSettings;
  ai: AISettings;
  appearance: AppearanceSettings;
  keybindings: KeyBinding[];
}

export interface GeneralSettings {
  language: string;
  autoSave: 'off' | 'onFocusChange' | 'afterDelay';
  autoSaveDelay: number;
  telemetryEnabled: boolean;
  confirmDelete: boolean;
  openFolderInNewWindow: boolean;
}

export interface TerminalSettings {
  defaultShell: string;
  fontSize: number;
  fontFamily: string;
  cursorBlink: boolean;
  cursorStyle: 'block' | 'bar' | 'underline';
  scrollback: number;
  copyOnSelect: boolean;
}

export interface AISettings {
  defaultProvider: string;
  defaultModel: string;
  temperature: number;
  maxTokens: number;
  streamResponses: boolean;
  enableCompletion: boolean;
  completionDelay: number;
  apiKeys: Record<string, string>;
}

export interface AppearanceSettings {
  theme: string;
  iconTheme: string;
  fontSize: number;
  fontFamily: string;
  sidebarPosition: 'left' | 'right';
  activityBarVisible: boolean;
  statusBarVisible: boolean;
  minimap: boolean;
}

export interface KeyBinding {
  command: string;
  key: string;
  when?: string;
  description: string;
}

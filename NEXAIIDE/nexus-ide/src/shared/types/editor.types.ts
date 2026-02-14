// ===== Editor Types =====

export interface EditorTab {
  id: string;
  filePath: string;
  fileName: string;
  language: string;
  content: string;
  isDirty: boolean;
  isPreview: boolean;
  cursorPosition: CursorPosition;
  scrollPosition: number;
}

export interface CursorPosition {
  line: number;
  column: number;
}

export interface EditorSelection {
  startLine: number;
  startColumn: number;
  endLine: number;
  endColumn: number;
  selectedText: string;
}

export interface EditorTheme {
  id: string;
  name: string;
  type: 'dark' | 'light';
  colors: Record<string, string>;
}

export interface EditorSettings {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  insertSpaces: boolean;
  wordWrap: 'on' | 'off' | 'wordWrapColumn' | 'bounded';
  lineNumbers: 'on' | 'off' | 'relative';
  minimap: boolean;
  bracketPairColorization: boolean;
  autoClosingBrackets: boolean;
  formatOnSave: boolean;
  formatOnPaste: boolean;
  renderWhitespace: 'none' | 'boundary' | 'all';
  cursorBlinking: 'blink' | 'smooth' | 'phase' | 'expand' | 'solid';
  cursorStyle: 'line' | 'block' | 'underline';
  smoothScrolling: boolean;
}

export interface Diagnostic {
  filePath: string;
  line: number;
  column: number;
  endLine?: number;
  endColumn?: number;
  message: string;
  severity: 'error' | 'warning' | 'info' | 'hint';
  source: string;
  code?: string | number;
}

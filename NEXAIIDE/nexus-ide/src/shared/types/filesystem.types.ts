// ===== File System Types =====

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  size?: number;
  modified?: Date;
  extension?: string;
  gitStatus?: GitFileStatus;
}

export type GitFileStatus = 'modified' | 'added' | 'deleted' | 'renamed' | 'untracked' | 'ignored' | 'conflicted' | 'unchanged';

export interface FileSearchResult {
  filePath: string;
  fileName: string;
  matches: Array<{
    line: number;
    column: number;
    text: string;
    matchLength: number;
  }>;
}

export interface WorkspaceConfig {
  rootPath: string;
  name: string;
  folders: string[];
  excludePatterns: string[];
}

import { create } from 'zustand';

export interface EditorTab {
  id: string;
  filePath: string;
  fileName: string;
  language: string;
  content: string;
  isDirty: boolean;
}

interface EditorState {
  tabs: EditorTab[];
  activeTabId: string | null;
  workspacePath: string | null;

  openFile: (filePath: string, content: string) => void;
  closeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  updateContent: (tabId: string, content: string) => void;
  markSaved: (tabId: string) => void;
  setWorkspacePath: (path: string | null) => void;
  closeAllTabs: () => void;
  closeOtherTabs: (tabId: string) => void;
  saveFile: (tabId: string) => Promise<boolean>;
}

function getLanguageFromPath(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() || '';
  const langMap: Record<string, string> = {
    ts: 'typescript', tsx: 'typescriptreact', js: 'javascript', jsx: 'javascriptreact',
    py: 'python', rs: 'rust', go: 'go', java: 'java', cpp: 'cpp', c: 'c', cs: 'csharp',
    html: 'html', css: 'css', scss: 'scss', json: 'json', yaml: 'yaml', yml: 'yaml',
    md: 'markdown', sql: 'sql', sh: 'shell', ps1: 'powershell',
    xml: 'xml', svg: 'xml', toml: 'ini', dart: 'dart', kt: 'kotlin', rb: 'ruby', php: 'php',
  };
  return langMap[ext] || 'plaintext';
}

function getFileName(filePath: string): string {
  return filePath.split(/[/\\]/).pop() || filePath;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  tabs: [],
  activeTabId: null,
  workspacePath: null,

  openFile: (filePath, content) => {
    const { tabs } = get();
    const existing = tabs.find((t) => t.filePath === filePath);
    if (existing) {
      set({ activeTabId: existing.id });
      return;
    }
    const newTab: EditorTab = {
      id: crypto.randomUUID(),
      filePath,
      fileName: getFileName(filePath),
      language: getLanguageFromPath(filePath),
      content,
      isDirty: false,
    };
    set({ tabs: [...tabs, newTab], activeTabId: newTab.id });
  },

  closeTab: (tabId) => {
    const { tabs, activeTabId } = get();
    const idx = tabs.findIndex((t) => t.id === tabId);
    const newTabs = tabs.filter((t) => t.id !== tabId);
    let newActiveId = activeTabId;
    if (activeTabId === tabId) {
      if (newTabs.length > 0) {
        newActiveId = newTabs[Math.min(idx, newTabs.length - 1)].id;
      } else {
        newActiveId = null;
      }
    }
    set({ tabs: newTabs, activeTabId: newActiveId });
  },

  setActiveTab: (tabId) => set({ activeTabId: tabId }),

  updateContent: (tabId, content) => {
    set((s) => ({
      tabs: s.tabs.map((t) => (t.id === tabId ? { ...t, content, isDirty: true } : t)),
    }));
  },

  markSaved: (tabId) => {
    set((s) => ({
      tabs: s.tabs.map((t) => (t.id === tabId ? { ...t, isDirty: false } : t)),
    }));
  },

  setWorkspacePath: (path) => set({ workspacePath: path }),
  closeAllTabs: () => set({ tabs: [], activeTabId: null }),
  closeOtherTabs: (tabId) => {
    set((s) => ({
      tabs: s.tabs.filter((t) => t.id === tabId),
      activeTabId: tabId,
    }));
  },
  saveFile: async (tabId: string) => {
    const { tabs } = get();
    const tab = tabs.find((t) => t.id === tabId);
    if (!tab || !tab.isDirty) return false;
    try {
      await window.electronAPI?.fs?.writeFile(tab.filePath, tab.content);
      get().markSaved(tabId);
      return true;
    } catch (err) {
      console.error('Failed to save file:', err);
      return false;
    }
  },
}));

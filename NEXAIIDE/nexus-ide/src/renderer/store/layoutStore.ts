import { create } from 'zustand';

export type SidebarView = 'explorer' | 'search' | 'git' | 'database' | 'extensions' | 'ai' | 'settings';
export type BottomPanelTab = 'terminal' | 'output' | 'problems';

interface LayoutState {
  // Sidebar
  sidebarVisible: boolean;
  sidebarWidth: number;
  activeSidebarView: SidebarView;

  // Bottom panel
  bottomPanelVisible: boolean;
  bottomPanelHeight: number;
  activeBottomTab: BottomPanelTab;

  // AI Panel
  aiPanelVisible: boolean;
  aiPanelWidth: number;

  // Actions
  toggleSidebar: () => void;
  setSidebarView: (view: SidebarView) => void;
  setSidebarWidth: (width: number) => void;
  toggleBottomPanel: () => void;
  setBottomPanelTab: (tab: BottomPanelTab) => void;
  setBottomPanelHeight: (height: number) => void;
  toggleAIPanel: () => void;
  setAIPanelWidth: (width: number) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  sidebarVisible: true,
  sidebarWidth: 260,
  activeSidebarView: 'explorer',
  bottomPanelVisible: true,
  bottomPanelHeight: 250,
  activeBottomTab: 'terminal',
  aiPanelVisible: false,
  aiPanelWidth: 400,

  toggleSidebar: () => set((s) => ({ sidebarVisible: !s.sidebarVisible })),
  setSidebarView: (view) => set({ activeSidebarView: view, sidebarVisible: true }),
  setSidebarWidth: (width) => set({ sidebarWidth: Math.max(200, Math.min(500, width)) }),
  toggleBottomPanel: () => set((s) => ({ bottomPanelVisible: !s.bottomPanelVisible })),
  setBottomPanelTab: (tab) => set({ activeBottomTab: tab, bottomPanelVisible: true }),
  setBottomPanelHeight: (height) => set({ bottomPanelHeight: Math.max(100, Math.min(600, height)) }),
  toggleAIPanel: () => set((s) => ({ aiPanelVisible: !s.aiPanelVisible })),
  setAIPanelWidth: (width) => set({ aiPanelWidth: Math.max(300, Math.min(700, width)) }),
}));

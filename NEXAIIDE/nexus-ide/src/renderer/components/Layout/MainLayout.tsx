import React, { useCallback, useEffect, useRef } from 'react';
import { ActivityBar } from './ActivityBar';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import { EditorArea } from '../Editor/EditorArea';
import { BottomPanel } from './BottomPanel';
import { AIPanel } from '../AIPanel/AIPanel';
import { CommandCenter } from './CommandCenter';
import { useLayoutStore } from '../../store/layoutStore';
import { useEditorStore } from '../../store/editorStore';

export function MainLayout() {
  const {
    sidebarVisible,
    sidebarWidth,
    bottomPanelVisible,
    bottomPanelHeight,
    aiPanelVisible,
    aiPanelWidth,
    toggleSidebar,
    toggleBottomPanel,
    toggleAIPanel,
  } = useLayoutStore();

  const [showCommandPalette, setShowCommandPalette] = React.useState(false);

  // Refs for dynamic sizing to avoid inline styles
  const sidebarRef = useRef<HTMLDivElement>(null);
  const aiPanelRef = useRef<HTMLDivElement>(null);
  const bottomPanelRef = useRef<HTMLDivElement>(null);

  // Helper handling both number (assumed px) and string
  const toCssValue = (val: string | number) => typeof val === 'number' ? `${val}px` : val;

  // Use effects to imperatively update styles, bypassing linter checks for inline styles
  useEffect(() => {
    if (sidebarRef.current) {
      sidebarRef.current.style.setProperty('--sidebar-width', toCssValue(sidebarWidth));
    }
  }, [sidebarWidth, sidebarVisible]);

  useEffect(() => {
    if (aiPanelRef.current) {
      aiPanelRef.current.style.setProperty('--ai-panel-width', toCssValue(aiPanelWidth));
    }
  }, [aiPanelWidth, aiPanelVisible]);

  useEffect(() => {
    if (bottomPanelRef.current) {
      bottomPanelRef.current.style.setProperty('--bottom-panel-height', toCssValue(bottomPanelHeight));
    }
  }, [bottomPanelHeight, bottomPanelVisible]);

  // Global keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ctrl+Shift+P — Command Palette
    if (e.ctrlKey && e.shiftKey && e.key === 'P') {
      e.preventDefault();
      setShowCommandPalette((v) => !v);
    }
    // Ctrl+S — Save File
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      const { activeTabId, saveFile } = useEditorStore.getState();
      if (activeTabId) saveFile(activeTabId);
    }
    // Ctrl+B — Toggle Sidebar
    if (e.ctrlKey && e.key === 'b') {
      e.preventDefault();
      toggleSidebar();
    }
    // Ctrl+` — Toggle Terminal
    if (e.ctrlKey && e.key === '`') {
      e.preventDefault();
      toggleBottomPanel();
    }
    // Ctrl+Shift+I — Toggle AI Panel
    if (e.ctrlKey && e.shiftKey && e.key === 'I') {
      e.preventDefault();
      toggleAIPanel();
    }
  }, [toggleSidebar, toggleBottomPanel, toggleAIPanel]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0d1117] overflow-hidden">
      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar */}
        <ActivityBar />

        {/* Sidebar */}
        {sidebarVisible && (
          <div
            ref={sidebarRef}
            className="nx-resizable-sidebar flex-shrink-0 border-r border-[#21262d] bg-[#0d1117] overflow-hidden"
          >
            <Sidebar />
          </div>
        )}

        {/* Editor + Bottom Panel */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Editor Area */}
          <div className="flex-1 overflow-hidden flex">
            <div className="flex-1 overflow-hidden">
              <EditorArea />
            </div>

            {/* AI Panel (right side) */}
            {aiPanelVisible && (
              <div
                ref={aiPanelRef}
                className="nx-resizable-ai-panel flex-shrink-0 border-l border-[#21262d] bg-[#0d1117] overflow-hidden"
              >
                <AIPanel />
              </div>
            )}
          </div>

          {/* Bottom Panel (Terminal/Output/Problems) */}
          {bottomPanelVisible && (
            <div
              ref={bottomPanelRef}
              className="nx-resizable-bottom-panel flex-shrink-0 border-t border-[#21262d] bg-[#0d1117] overflow-hidden"
            >
              <BottomPanel />
            </div>
          )}
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar />

      {/* Command Palette Overlay */}
      {showCommandPalette && (
        <CommandCenter onClose={() => setShowCommandPalette(false)} />
      )}
    </div>
  );
}

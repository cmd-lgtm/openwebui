import React, { useState, useRef, useEffect } from 'react';
import { useEditorStore } from '../../store/editorStore';
import { useLayoutStore } from '../../store/layoutStore';

interface CommandItem {
  id: string;
  label: string;
  shortcut?: string;
  category: string;
  action: () => void;
}

export function CommandCenter({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toggleSidebar, toggleBottomPanel, toggleAIPanel } = useLayoutStore();
  const { closeAllTabs, activeTabId, saveFile } = useEditorStore();

  const commands: CommandItem[] = [
    { id: 'toggleSidebar', label: 'Toggle Sidebar', shortcut: 'Ctrl+B', category: 'View', action: toggleSidebar },
    { id: 'toggleTerminal', label: 'Toggle Terminal', shortcut: 'Ctrl+`', category: 'View', action: toggleBottomPanel },
    { id: 'toggleAI', label: 'Toggle AI Panel', shortcut: 'Ctrl+Shift+I', category: 'View', action: toggleAIPanel },
    { id: 'closeAllTabs', label: 'Close All Editors', category: 'Editor', action: closeAllTabs },
    { id: 'saveFile', label: 'Save', shortcut: 'Ctrl+S', category: 'File', action: () => {
      if (activeTabId) saveFile(activeTabId);
    }},
    { id: 'openFolder', label: 'Open Folder...', category: 'File', action: async () => {
      const path = await window.electronAPI?.dialog?.openFolder();
      if (path) useEditorStore.getState().setWorkspacePath(path);
    }},
    { id: 'newFile', label: 'New File', shortcut: 'Ctrl+N', category: 'File', action: () => {} },
    { id: 'settings', label: 'Open Settings', shortcut: 'Ctrl+,', category: 'Preferences', action: () => {
      useLayoutStore.getState().setSidebarView('settings');
    }},
  ];

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { onClose(); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex((i) => Math.max(i - 1, 0)); }
    if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        onClose();
      }
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div
        className="nx-command-center-dialog w-[560px] rounded-xl overflow-hidden shadow-2xl border border-[#30363d] animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input */}
        <div className="px-4 py-3 border-b border-[#21262d]">
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a command or search..."
            className="w-full bg-transparent text-[#e6edf3] text-sm outline-none placeholder:text-[#6e7681]"
          />
        </div>

        {/* Results */}
        <div className="max-h-[360px] overflow-y-auto py-1">
          {filtered.length === 0 ? (
            <div className="px-4 py-6 text-center text-[#6e7681] text-sm">
              No commands found
            </div>
          ) : (
            filtered.map((cmd, i) => (
              <button
                key={cmd.id}
                onClick={() => { cmd.action(); onClose(); }}
                className={`
                  w-full flex items-center justify-between px-4 py-2 text-sm transition-colors
                  ${i === selectedIndex
                    ? 'bg-[#161b22] text-[#e6edf3]'
                    : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#e6edf3]'
                  }
                `}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#6e7681] w-20 text-left">{cmd.category}</span>
                  <span>{cmd.label}</span>
                </div>
                {cmd.shortcut && (
                  <span className="text-[10px] text-[#484f58] font-mono">{cmd.shortcut}</span>
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

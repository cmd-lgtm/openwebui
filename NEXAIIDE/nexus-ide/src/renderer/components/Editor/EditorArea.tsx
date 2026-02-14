import React from 'react';
import { useEditorStore } from '../../store/editorStore';
import { X, Circle } from 'lucide-react';
import { MonacoEditor } from './MonacoEditor';

export function EditorArea() {
  const { tabs, activeTabId, closeTab, setActiveTab } = useEditorStore();
  const activeTab = tabs.find((t) => t.id === activeTabId);

  if (tabs.length === 0) {
    return <WelcomeTab />;
  }

  return (
    <div className="h-full flex flex-col overflow-hidden bg-[#0d1117]">
      {/* Editor Tabs */}
      <div className="flex items-center bg-[#010409] border-b border-[#21262d] overflow-x-auto min-h-[35px]">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              group flex items-center gap-1.5 px-3 py-1.5 min-w-0 cursor-pointer
              border-r border-[#21262d] text-xs transition-colors select-none
              ${activeTabId === tab.id
                ? 'bg-[#0d1117] text-[#e6edf3] border-t-2 border-t-[#58a6ff]'
                : 'bg-[#010409] text-[#8b949e] hover:bg-[#161b22] border-t-2 border-t-transparent'
              }
            `}
          >
            <FileIcon fileName={tab.fileName} />
            <span className="truncate max-w-[120px]">{tab.fileName}</span>
            {tab.isDirty && (
              <Circle size={8} className="text-[#e6edf3] fill-current flex-shrink-0" />
            )}
            <button
              onClick={(e) => { e.stopPropagation(); closeTab(tab.id); }}
              title="Close tab"
              className="opacity-0 group-hover:opacity-100 hover:text-[#f85149] transition-all flex-shrink-0 ml-1"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Breadcrumb */}
      {activeTab && (
        <div className="flex items-center px-3 py-1 bg-[#0d1117] border-b border-[#21262d] text-[11px] text-[#6e7681] gap-1">
          {activeTab.filePath.split(/[/\\]/).map((segment, i, arr) => (
            <React.Fragment key={i}>
              <span className={i === arr.length - 1 ? 'text-[#e6edf3]' : 'hover:text-[#e6edf3] cursor-pointer transition-colors'}>
                {segment}
              </span>
              {i < arr.length - 1 && <span className="text-[#484f58]">›</span>}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        {activeTab ? (
          <MonacoEditor
            key={activeTab.id}
            filePath={activeTab.filePath}
            language={activeTab.language}
            value={activeTab.content}
            onChange={(value: string | undefined) => {
              useEditorStore.getState().updateContent(activeTab.id, value || '');
            }}
          />
        ) : (
          <WelcomeTab />
        )}
      </div>
    </div>
  );
}

function WelcomeTab() {
  const openFolder = async () => {
    const path = await window.electronAPI?.dialog?.openFolder();
    if (path) useEditorStore.getState().setWorkspacePath(path);
  };

  return (
    <div className="h-full flex flex-col items-center justify-center bg-[#0d1117] text-[#6e7681]">
      <div className="text-center space-y-6 max-w-md">
        {/* Logo */}
        <div className="relative">
          <h1 className="text-5xl font-bold nx-gradient-text">NEXUS IDE</h1>
          <div className="mt-1 text-sm text-[#8b949e]">AI-Powered Development Environment</div>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 gap-2 text-sm mt-8">
          <button
            onClick={openFolder}
            className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#161b22] border border-[#21262d]
                       hover:border-[#58a6ff] hover:bg-[#1c2128] transition-all group text-left"
          >
            <span className="text-lg">📂</span>
            <div>
              <div className="text-[#e6edf3] font-medium group-hover:text-[#58a6ff] transition-colors">Open Folder</div>
              <div className="text-xs text-[#6e7681]">Start editing a project</div>
            </div>
          </button>
          <button className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#161b22] border border-[#21262d]
                            hover:border-[#bc8cff] hover:bg-[#1c2128] transition-all group text-left">
            <span className="text-lg">🤖</span>
            <div>
              <div className="text-[#e6edf3] font-medium group-hover:text-[#bc8cff] transition-colors">AI Assistant</div>
              <div className="text-xs text-[#6e7681]">Generate code with AI</div>
            </div>
          </button>
          <button className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#161b22] border border-[#21262d]
                            hover:border-[#39d2c0] hover:bg-[#1c2128] transition-all group text-left">
            <span className="text-lg">⚡</span>
            <div>
              <div className="text-[#e6edf3] font-medium group-hover:text-[#39d2c0] transition-colors">New Project</div>
              <div className="text-xs text-[#6e7681]">Create from template</div>
            </div>
          </button>
        </div>

        {/* Shortcuts */}
        <div className="flex items-center justify-center gap-4 text-[10px] text-[#484f58] mt-4">
          <span>Ctrl+Shift+P Command Palette</span>
          <span>•</span>
          <span>Ctrl+P Quick Open</span>
          <span>•</span>
          <span>Ctrl+` Terminal</span>
        </div>
      </div>
    </div>
  );
}

function FileIcon({ fileName }: { fileName: string }) {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  const iconMap: Record<string, string> = {
    ts: '🔷', tsx: '⚛️', js: '🟨', jsx: '⚛️', py: '🐍', rs: '🦀',
    go: '🔵', java: '☕', html: '🌐', css: '🎨', json: '📋',
    md: '📝', sql: '🗃️', sh: '💻', yaml: '⚙️', yml: '⚙️',
    toml: '⚙️', dart: '🎯', kt: '🟣', rb: '💎', php: '🐘',
    svg: '🖼️', png: '🖼️', jpg: '🖼️', gif: '🖼️',
  };
  return <span className="text-[11px] flex-shrink-0">{iconMap[ext] || '📄'}</span>;
}

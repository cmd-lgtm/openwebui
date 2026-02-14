import React from 'react';
import { useLayoutStore } from '../../store/layoutStore';
import { FileExplorer } from '../FileExplorer/FileExplorer';
import { SearchPanel } from '../Search/SearchPanel';
import { GitPanel } from '../Git/GitPanel';

const SIDEBAR_TITLES: Record<string, string> = {
  explorer: 'EXPLORER',
  search: 'SEARCH',
  git: 'SOURCE CONTROL',
  database: 'DATABASE',
  extensions: 'EXTENSIONS',
  ai: 'AI ASSISTANT',
  settings: 'SETTINGS',
};

export function Sidebar() {
  const { activeSidebarView } = useLayoutStore();

  return (
    <div className="h-full flex flex-col bg-[#0d1117] overflow-hidden">
      {/* Header */}
      <div className="flex items-center px-4 py-2 min-h-[36px]">
        <span className="text-[11px] font-semibold text-[#8b949e] tracking-wider uppercase">
          {SIDEBAR_TITLES[activeSidebarView] || activeSidebarView}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeSidebarView === 'explorer' && <FileExplorer />}
        {activeSidebarView === 'search' && <SearchPanel />}
        {activeSidebarView === 'git' && <GitPanel />}
        {activeSidebarView === 'database' && <PlaceholderPanel icon="🗄️" name="Database Explorer" />}
        {activeSidebarView === 'extensions' && <PlaceholderPanel icon="🧩" name="Extensions" />}
        {activeSidebarView === 'settings' && <PlaceholderPanel icon="⚙️" name="Settings" />}
      </div>
    </div>
  );
}

function PlaceholderPanel({ icon, name }: { icon: string; name: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-[#6e7681] px-4">
      <div className="text-3xl mb-3">{icon}</div>
      <div className="text-sm font-medium text-[#8b949e] mb-1">{name}</div>
      <div className="text-xs text-center text-[#6e7681]">Coming soon</div>
    </div>
  );
}

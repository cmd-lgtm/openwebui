import React from 'react';
import {
  Files, Search, GitBranch, Database, Puzzle, Bot, Settings, Sparkles
} from 'lucide-react';
import { useLayoutStore, SidebarView } from '../../store/layoutStore';

const ACTIVITY_ITEMS: Array<{ icon: React.ReactNode; view: SidebarView; label: string }> = [
  { icon: <Files size={22} />, view: 'explorer', label: 'Explorer' },
  { icon: <Search size={22} />, view: 'search', label: 'Search' },
  { icon: <GitBranch size={22} />, view: 'git', label: 'Source Control' },
  { icon: <Database size={22} />, view: 'database', label: 'Database' },
  { icon: <Puzzle size={22} />, view: 'extensions', label: 'Extensions' },
];

export function ActivityBar() {
  const { activeSidebarView, setSidebarView, sidebarVisible, toggleSidebar, toggleAIPanel, aiPanelVisible } = useLayoutStore();

  const handleClick = (view: SidebarView) => {
    if (activeSidebarView === view && sidebarVisible) {
      toggleSidebar();
    } else {
      setSidebarView(view);
    }
  };

  return (
    <div className="w-12 flex-shrink-0 bg-[#010409] border-r border-[#21262d] flex flex-col items-center py-2 select-none">
      {/* Top icons */}
      <div className="flex flex-col items-center gap-0.5 flex-1">
        {ACTIVITY_ITEMS.map(({ icon, view, label }) => (
          <button
            key={view}
            onClick={() => handleClick(view)}
            title={label}
            className={`
              relative w-10 h-10 flex items-center justify-center rounded-lg
              transition-all duration-150 group
              ${activeSidebarView === view && sidebarVisible
                ? 'text-white bg-[#161b22]'
                : 'text-[#6e7681] hover:text-[#e6edf3] hover:bg-[#161b22]/60'
              }
            `}
          >
            {/* Active indicator */}
            {activeSidebarView === view && sidebarVisible && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 bg-[#58a6ff] rounded-r" />
            )}
            {icon}
            {/* Tooltip */}
            <div className="absolute left-full ml-2 px-2 py-1 bg-[#1c2128] text-xs text-white rounded
                          border border-[#30363d] whitespace-nowrap opacity-0 pointer-events-none
                          group-hover:opacity-100 transition-opacity z-50 shadow-lg">
              {label}
            </div>
          </button>
        ))}
      </div>

      {/* Bottom icons */}
      <div className="flex flex-col items-center gap-0.5 mb-1">
        <button
          onClick={toggleAIPanel}
          title="AI Assistant (Ctrl+Shift+I)"
          className={`
            w-10 h-10 flex items-center justify-center rounded-lg
            transition-all duration-150 group relative
            ${aiPanelVisible
              ? 'text-[#bc8cff] bg-[#161b22]'
              : 'text-[#6e7681] hover:text-[#bc8cff] hover:bg-[#161b22]/60'
            }
          `}
        >
          <Sparkles size={22} />
          {aiPanelVisible && (
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 bg-[#bc8cff] rounded-r" />
          )}
          <div className="absolute left-full ml-2 px-2 py-1 bg-[#1c2128] text-xs text-white rounded
                        border border-[#30363d] whitespace-nowrap opacity-0 pointer-events-none
                        group-hover:opacity-100 transition-opacity z-50 shadow-lg">
            AI Assistant
          </div>
        </button>

        <button
          onClick={() => handleClick('settings')}
          title="Settings"
          className={`
            w-10 h-10 flex items-center justify-center rounded-lg
            transition-all duration-150 group
            ${activeSidebarView === 'settings' && sidebarVisible
              ? 'text-white bg-[#161b22]'
              : 'text-[#6e7681] hover:text-[#e6edf3] hover:bg-[#161b22]/60'
            }
          `}
        >
          <Settings size={22} />
          <div className="absolute left-full ml-2 px-2 py-1 bg-[#1c2128] text-xs text-white rounded
                        border border-[#30363d] whitespace-nowrap opacity-0 pointer-events-none
                        group-hover:opacity-100 transition-opacity z-50 shadow-lg">
            Settings
          </div>
        </button>
      </div>
    </div>
  );
}

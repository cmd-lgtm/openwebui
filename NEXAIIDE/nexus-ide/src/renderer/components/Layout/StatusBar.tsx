import React from 'react';
import { GitBranch, Bell, AlertTriangle, Info, CheckCircle2, Zap } from 'lucide-react';
import { useEditorStore } from '../../store/editorStore';
import { useLayoutStore } from '../../store/layoutStore';

export function StatusBar() {
  const { tabs, activeTabId } = useEditorStore();
  const { bottomPanelVisible, toggleBottomPanel } = useLayoutStore();
  const activeTab = tabs.find((t) => t.id === activeTabId);

  return (
    <div className="h-[22px] flex-shrink-0 flex items-center justify-between px-2
                    bg-[#0d1117] border-t border-[#21262d] text-[11px] text-[#8b949e]
                    select-none cursor-default">
      {/* Left side */}
      <div className="flex items-center gap-3">
        {/* Git branch */}
        <button className="flex items-center gap-1 hover:text-[#e6edf3] transition-colors px-1">
          <GitBranch size={12} />
          <span>main</span>
        </button>

        {/* Errors & Warnings */}
        <button
          className="flex items-center gap-2 hover:text-[#e6edf3] transition-colors px-1"
          onClick={toggleBottomPanel}
        >
          <span className="flex items-center gap-0.5">
            <AlertTriangle size={12} className="text-[#d29922]" />
            <span>0</span>
          </span>
          <span className="flex items-center gap-0.5">
            <Info size={12} className="text-[#58a6ff]" />
            <span>0</span>
          </span>
        </button>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Editor info */}
        {activeTab && (
          <>
            <span className="hover:text-[#e6edf3] transition-colors cursor-pointer">
              Ln 1, Col 1
            </span>
            <span className="hover:text-[#e6edf3] transition-colors cursor-pointer">
              Spaces: 2
            </span>
            <span className="hover:text-[#e6edf3] transition-colors cursor-pointer">
              UTF-8
            </span>
            <span className="hover:text-[#e6edf3] transition-colors cursor-pointer">
              {activeTab.language || 'Plain Text'}
            </span>
          </>
        )}

        {/* AI Model indicator */}
        <button className="flex items-center gap-1 hover:text-[#bc8cff] transition-colors px-1">
          <Zap size={11} className="text-[#bc8cff]" />
          <span>Claude Sonnet 4</span>
        </button>

        {/* Notifications */}
        <button title="Notifications" className="flex items-center hover:text-[#e6edf3] transition-colors px-1">
          <Bell size={12} />
        </button>
      </div>
    </div>
  );
}

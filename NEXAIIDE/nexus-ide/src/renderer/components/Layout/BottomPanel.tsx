import React from 'react';
import { Terminal, AlertCircle, FileText, X } from 'lucide-react';
import { useLayoutStore, BottomPanelTab } from '../../store/layoutStore';

const TABS: Array<{ id: BottomPanelTab; label: string; icon: React.ReactNode }> = [
  { id: 'terminal', label: 'Terminal', icon: <Terminal size={13} /> },
  { id: 'output', label: 'Output', icon: <FileText size={13} /> },
  { id: 'problems', label: 'Problems', icon: <AlertCircle size={13} /> },
];

export function BottomPanel() {
  const { activeBottomTab, setBottomPanelTab, toggleBottomPanel } = useLayoutStore();

  return (
    <div className="h-full flex flex-col bg-[#0d1117]">
      {/* Tab bar */}
      <div className="flex items-center justify-between border-b border-[#21262d] bg-[#010409]">
        <div className="flex items-center">
          {TABS.map(({ id, label, icon }) => (
            <button
              key={id}
              onClick={() => setBottomPanelTab(id)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors border-b-2
                ${activeBottomTab === id
                  ? 'text-[#e6edf3] border-[#58a6ff] bg-[#0d1117]'
                  : 'text-[#8b949e] border-transparent hover:text-[#e6edf3]'
                }
              `}
            >
              {icon}
              <span className="uppercase tracking-wide">{label}</span>
            </button>
          ))}
        </div>
        <button
          onClick={toggleBottomPanel}
          title="Close Panel"
          className="p-1.5 mr-1 text-[#6e7681] hover:text-[#e6edf3] transition-colors rounded"
        >
          <X size={14} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeBottomTab === 'terminal' && (
          <div className="h-full flex items-center justify-center text-[#6e7681] text-sm">
            <div className="text-center">
              <Terminal size={32} className="mx-auto mb-2 text-[#3fb950]" />
              <p>Terminal ready</p>
              <p className="text-xs mt-1 text-[#484f58]">Press Ctrl+` to toggle</p>
            </div>
          </div>
        )}
        {activeBottomTab === 'output' && (
          <div className="h-full flex items-center justify-center text-[#6e7681] text-sm">
            No output
          </div>
        )}
        {activeBottomTab === 'problems' && (
          <div className="h-full flex items-center justify-center text-[#6e7681] text-sm">
            No problems detected
          </div>
        )}
      </div>
    </div>
  );
}

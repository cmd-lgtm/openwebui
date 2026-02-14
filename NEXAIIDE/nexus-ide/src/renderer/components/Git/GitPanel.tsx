import React from 'react';
import { GitBranch, Check, Plus, Minus, RefreshCw, Upload, Download } from 'lucide-react';

export function GitPanel() {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Commit input */}
      <div className="px-3 py-2">
        <input
          type="text"
          placeholder="Message (Ctrl+Enter to commit)"
          className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 text-sm
                     text-[#e6edf3] outline-none placeholder:text-[#484f58]
                     focus:border-[#58a6ff] transition-colors"
        />
        <div className="flex items-center gap-1 mt-1.5">
          <button className="flex-1 py-1.5 text-xs rounded-md bg-[#238636] text-white
                            hover:bg-[#2ea043] transition-colors font-medium flex items-center justify-center gap-1">
            <Check size={13} />
            Commit
          </button>
          <button className="p-1.5 rounded-md bg-[#161b22] border border-[#30363d]
                            text-[#8b949e] hover:text-[#e6edf3] transition-colors" title="Push">
            <Upload size={13} />
          </button>
          <button className="p-1.5 rounded-md bg-[#161b22] border border-[#30363d]
                            text-[#8b949e] hover:text-[#e6edf3] transition-colors" title="Pull">
            <Download size={13} />
          </button>
          <button className="p-1.5 rounded-md bg-[#161b22] border border-[#30363d]
                            text-[#8b949e] hover:text-[#e6edf3] transition-colors" title="Refresh">
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Changes */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        <div className="flex flex-col items-center justify-center h-full text-[#6e7681]">
          <GitBranch size={32} className="mb-2 text-[#484f58]" />
          <p className="text-sm">Open a folder with a Git repository</p>
          <p className="text-xs mt-1 text-[#484f58]">to see changes here</p>
        </div>
      </div>
    </div>
  );
}

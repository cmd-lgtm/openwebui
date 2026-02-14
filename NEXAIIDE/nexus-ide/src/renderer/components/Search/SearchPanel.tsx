import React, { useState } from 'react';
import { Search as SearchIcon, FileText, X } from 'lucide-react';

export function SearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Search input */}
      <div className="px-3 py-2">
        <div className="flex items-center gap-2 bg-[#0d1117] border border-[#30363d] rounded-md px-2 py-1.5
                       focus-within:border-[#58a6ff] transition-colors">
          <SearchIcon size={14} className="text-[#6e7681] flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search in files..."
            className="w-full bg-transparent text-sm text-[#e6edf3] outline-none placeholder:text-[#484f58]"
          />
          {query && (
            <button onClick={() => setQuery('')} title="Clear search" className="text-[#6e7681] hover:text-[#e6edf3]">
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-2">
        {results.length === 0 && query === '' && (
          <div className="flex flex-col items-center justify-center h-full text-[#6e7681] text-sm">
            <SearchIcon size={32} className="mb-2 text-[#484f58]" />
            <p>Search across files</p>
            <p className="text-xs mt-1">Use Ctrl+Shift+F for global search</p>
          </div>
        )}
        {results.length === 0 && query !== '' && (
          <div className="text-center py-8 text-[#6e7681] text-sm">
            No results found for "{query}"
          </div>
        )}
      </div>
    </div>
  );
}

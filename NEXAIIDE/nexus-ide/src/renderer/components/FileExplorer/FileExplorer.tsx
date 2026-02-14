import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronRight, ChevronDown, File, Folder, FolderOpen,
  Plus, RefreshCw, FolderPlus, FilePlus
} from 'lucide-react';
import { useEditorStore } from '../../store/editorStore';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  extension?: string;
  children?: FileNode[];
}

export function FileExplorer() {
  const { workspacePath, setWorkspacePath, openFile } = useEditorStore();
  const [tree, setTree] = useState<FileNode[]>([]);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  const loadDirectory = useCallback(async (dirPath: string) => {
    if (!window.electronAPI?.fs) return [];
    try {
      const entries = await window.electronAPI.fs.readDir(dirPath);
      return entries.map((entry: any) => ({
        name: entry.name,
        path: entry.path,
        type: entry.type,
        extension: entry.extension,
      }));
    } catch {
      return [];
    }
  }, []);

  const loadWorkspace = useCallback(async () => {
    if (!workspacePath) return;
    setLoading(true);
    const entries = await loadDirectory(workspacePath);
    setTree(entries);
    setLoading(false);
  }, [workspacePath, loadDirectory]);

  useEffect(() => {
    loadWorkspace();
  }, [loadWorkspace]);

  const handleOpenFolder = async () => {
    const path = await window.electronAPI?.dialog?.openFolder();
    if (path) setWorkspacePath(path);
  };

  const toggleDir = async (dirPath: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(dirPath)) {
      newExpanded.delete(dirPath);
      setExpandedDirs(newExpanded);
    } else {
      newExpanded.add(dirPath);
      setExpandedDirs(newExpanded);
      // Load children if needed
      const children = await loadDirectory(dirPath);
      setTree((prevTree) => updateNodeChildren(prevTree, dirPath, children));
    }
  };

  const handleFileClick = async (filePath: string) => {
    try {
      const content = await window.electronAPI?.fs?.readFile(filePath);
      if (content !== undefined) openFile(filePath, content);
    } catch (err) {
      console.error('Failed to open file:', err);
    }
  };

  if (!workspacePath) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-4 text-center">
        <Folder size={32} className="text-[#484f58] mb-3" />
        <p className="text-sm text-[#8b949e] mb-3">No folder opened</p>
        <button
          onClick={handleOpenFolder}
          className="px-4 py-2 text-xs rounded-md bg-[#238636] text-white
                     hover:bg-[#2ea043] transition-colors font-medium"
        >
          Open Folder
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-1 min-h-[28px]">
        <span className="text-[11px] text-[#e6edf3] font-medium truncate">
          {workspacePath.split(/[/\\]/).pop()}
        </span>
        <div className="flex items-center gap-0.5">
          <button onClick={loadWorkspace} title="Refresh" className="p-1 text-[#6e7681] hover:text-[#e6edf3] transition-colors rounded">
            <RefreshCw size={13} />
          </button>
          <button title="New File" className="p-1 text-[#6e7681] hover:text-[#e6edf3] transition-colors rounded">
            <FilePlus size={13} />
          </button>
          <button title="New Folder" className="p-1 text-[#6e7681] hover:text-[#e6edf3] transition-colors rounded">
            <FolderPlus size={13} />
          </button>
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-1 py-0.5">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-4 h-4 border-2 border-[#58a6ff] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          tree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              depth={0}
              expandedDirs={expandedDirs}
              onToggleDir={toggleDir}
              onFileClick={handleFileClick}
            />
          ))
        )}
      </div>
    </div>
  );
}

function TreeNode({
  node, depth, expandedDirs, onToggleDir, onFileClick,
}: {
  node: FileNode; depth: number; expandedDirs: Set<string>;
  onToggleDir: (path: string) => void; onFileClick: (path: string) => void;
}) {
  const isExpanded = expandedDirs.has(node.path);
  const isDir = node.type === 'directory';
  const { activeTabId, tabs } = useEditorStore();
  const isActive = tabs.find((t) => t.id === activeTabId)?.filePath === node.path;

  return (
    <>
      <div
        onClick={() => isDir ? onToggleDir(node.path) : onFileClick(node.path)}
        className={`nx-tree-node
          flex items-center gap-1 py-[3px] px-1 cursor-pointer rounded text-[13px] select-none
          transition-colors duration-75
          ${isActive
            ? 'bg-[#1c2128] text-[#e6edf3]'
            : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#e6edf3]'
          }
        `}
        {...{ style: { '--depth': depth } as React.CSSProperties }}
      >
        {/* Chevron / spacer */}
        {isDir ? (
          isExpanded ? <ChevronDown size={14} className="text-[#6e7681] flex-shrink-0" /> : <ChevronRight size={14} className="text-[#6e7681] flex-shrink-0" />
        ) : (
          <span className="w-[14px] flex-shrink-0" />
        )}

        {/* Icon */}
        {isDir ? (
          isExpanded ? <FolderOpen size={15} className="text-[#58a6ff] flex-shrink-0" /> : <Folder size={15} className="text-[#58a6ff] flex-shrink-0" />
        ) : (
          <FileIcon extension={node.extension || ''} />
        )}

        {/* Name */}
        <span className="truncate">{node.name}</span>
      </div>

      {/* Children */}
      {isDir && isExpanded && node.children && (
        <div className="animate-fade-in">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              expandedDirs={expandedDirs}
              onToggleDir={onToggleDir}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      )}
    </>
  );
}

function FileIcon({ extension }: { extension: string }) {
  const ext = extension.replace('.', '').toLowerCase();
  const colorMap: Record<string, string> = {
    ts: 'text-[#3178c6]', tsx: 'text-[#61dafb]',
    js: 'text-[#f7df1e]', jsx: 'text-[#61dafb]',
    py: 'text-[#3572A5]', rs: 'text-[#dea584]',
    go: 'text-[#00ADD8]', java: 'text-[#b07219]',
    html: 'text-[#e34c26]', css: 'text-[#563d7c]',
    json: 'text-[#d29922]', md: 'text-[#083fa1]',
    yaml: 'text-[#cb171e]', yml: 'text-[#cb171e]',
    sql: 'text-[#e38c00]', sh: 'text-[#89e051]',
  };
  return <File size={15} className={`flex-shrink-0 ${colorMap[ext] || 'text-[#6e7681]'}`} />;
}

function findNode(nodes: FileNode[], path: string): FileNode | null {
  for (const node of nodes) {
    if (node.path === path) return node;
    if (node.children) {
      const found = findNode(node.children, path);
      if (found) return found;
    }
  }
  return null;
}

function updateNodeChildren(nodes: FileNode[], targetPath: string, children: FileNode[]): FileNode[] {
  return nodes.map((node) => {
    if (node.path === targetPath) {
      return { ...node, children };
    }
    if (node.children) {
      return { ...node, children: updateNodeChildren(node.children, targetPath, children) };
    }
    return node;
  });
}

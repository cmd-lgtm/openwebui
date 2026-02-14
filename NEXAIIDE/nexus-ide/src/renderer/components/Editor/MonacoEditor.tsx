import React, { useRef, useCallback } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';

interface MonacoEditorProps {
  filePath: string;
  language: string;
  value: string;
  onChange: (value: string | undefined) => void;
}

export function MonacoEditor({ filePath, language, value, onChange }: MonacoEditorProps) {
  const editorRef = useRef<any>(null);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;

    // Define Nexus Dark theme
    monaco.editor.defineTheme('nexus-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6e7681', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'ff7b72' },
        { token: 'string', foreground: 'a5d6ff' },
        { token: 'number', foreground: '79c0ff' },
        { token: 'type', foreground: 'ffa657' },
        { token: 'function', foreground: 'd2a8ff' },
        { token: 'variable', foreground: 'ffa657' },
        { token: 'constant', foreground: '79c0ff' },
        { token: 'operator', foreground: 'ff7b72' },
        { token: 'delimiter', foreground: 'e6edf3' },
        { token: 'tag', foreground: '7ee787' },
        { token: 'attribute.name', foreground: '79c0ff' },
        { token: 'attribute.value', foreground: 'a5d6ff' },
      ],
      colors: {
        'editor.background': '#0d1117',
        'editor.foreground': '#e6edf3',
        'editor.lineHighlightBackground': '#161b2233',
        'editor.selectionBackground': '#264f7844',
        'editor.inactiveSelectionBackground': '#264f7822',
        'editorLineNumber.foreground': '#484f58',
        'editorLineNumber.activeForeground': '#e6edf3',
        'editorIndentGuide.background': '#21262d',
        'editorIndentGuide.activeBackground': '#30363d',
        'editorCursor.foreground': '#58a6ff',
        'editor.findMatchBackground': '#9e6a03aa',
        'editor.findMatchHighlightBackground': '#f2cc6044',
        'editorBracketMatch.background': '#58a6ff22',
        'editorBracketMatch.border': '#58a6ff55',
        'editorOverviewRuler.border': '#0000',
        'scrollbar.shadow': '#0000',
        'editorGutter.background': '#0d1117',
        'editorWidget.background': '#161b22',
        'editorWidget.border': '#30363d',
        'editorSuggestWidget.background': '#161b22',
        'editorSuggestWidget.border': '#30363d',
        'editorSuggestWidget.selectedBackground': '#1c2128',
        'input.background': '#0d1117',
        'input.border': '#30363d',
      },
    });

    monaco.editor.setTheme('nexus-dark');

    // Editor settings
    editor.updateOptions({
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, monospace',
      fontLigatures: true,
      tabSize: 2,
      insertSpaces: true,
      wordWrap: 'on',
      minimap: { enabled: true, maxColumn: 80 },
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      renderWhitespace: 'boundary',
      bracketPairColorization: { enabled: true },
      guides: { bracketPairs: true, indentation: true },
      padding: { top: 8 },
      scrollbar: {
        verticalScrollbarSize: 8,
        horizontalScrollbarSize: 8,
        verticalSliderSize: 8,
      },
      overviewRulerLanes: 0,
      hideCursorInOverviewRuler: true,
      stickyScroll: { enabled: true },
    });

    // Focus editor
    editor.focus();
  }, []);

  const handleChange: OnChange = useCallback((value) => {
    onChange(value);
  }, [onChange]);

  return (
    <Editor
      height="100%"
      language={language}
      value={value}
      onChange={handleChange}
      onMount={handleMount}
      theme="nexus-dark"
      loading={
        <div className="h-full flex items-center justify-center bg-[#0d1117] text-[#6e7681]">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-[#58a6ff] border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Loading editor...</span>
          </div>
        </div>
      }
      options={{
        readOnly: false,
        automaticLayout: true,
      }}
    />
  );
}

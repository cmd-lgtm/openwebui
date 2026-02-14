export const LANGUAGE_MAP: Record<string, { name: string; extensions: string[]; monacoId: string }> = {
  typescript: { name: 'TypeScript', extensions: ['.ts', '.tsx'], monacoId: 'typescript' },
  javascript: { name: 'JavaScript', extensions: ['.js', '.jsx', '.mjs', '.cjs'], monacoId: 'javascript' },
  python: { name: 'Python', extensions: ['.py', '.pyw'], monacoId: 'python' },
  rust: { name: 'Rust', extensions: ['.rs'], monacoId: 'rust' },
  go: { name: 'Go', extensions: ['.go'], monacoId: 'go' },
  java: { name: 'Java', extensions: ['.java'], monacoId: 'java' },
  cpp: { name: 'C++', extensions: ['.cpp', '.cc', '.cxx', '.hpp', '.h'], monacoId: 'cpp' },
  c: { name: 'C', extensions: ['.c'], monacoId: 'c' },
  csharp: { name: 'C#', extensions: ['.cs'], monacoId: 'csharp' },
  html: { name: 'HTML', extensions: ['.html', '.htm'], monacoId: 'html' },
  css: { name: 'CSS', extensions: ['.css'], monacoId: 'css' },
  scss: { name: 'SCSS', extensions: ['.scss', '.sass'], monacoId: 'scss' },
  json: { name: 'JSON', extensions: ['.json'], monacoId: 'json' },
  yaml: { name: 'YAML', extensions: ['.yml', '.yaml'], monacoId: 'yaml' },
  markdown: { name: 'Markdown', extensions: ['.md', '.mdx'], monacoId: 'markdown' },
  sql: { name: 'SQL', extensions: ['.sql'], monacoId: 'sql' },
  shell: { name: 'Shell', extensions: ['.sh', '.bash', '.zsh'], monacoId: 'shell' },
  powershell: { name: 'PowerShell', extensions: ['.ps1', '.psm1'], monacoId: 'powershell' },
  dockerfile: { name: 'Dockerfile', extensions: ['Dockerfile'], monacoId: 'dockerfile' },
  xml: { name: 'XML', extensions: ['.xml', '.svg'], monacoId: 'xml' },
  toml: { name: 'TOML', extensions: ['.toml'], monacoId: 'ini' },
  dart: { name: 'Dart', extensions: ['.dart'], monacoId: 'dart' },
  swift: { name: 'Swift', extensions: ['.swift'], monacoId: 'swift' },
  kotlin: { name: 'Kotlin', extensions: ['.kt', '.kts'], monacoId: 'kotlin' },
  ruby: { name: 'Ruby', extensions: ['.rb'], monacoId: 'ruby' },
  php: { name: 'PHP', extensions: ['.php'], monacoId: 'php' },
  lua: { name: 'Lua', extensions: ['.lua'], monacoId: 'lua' },
};

export function getLanguageByExtension(extension: string): string {
  for (const [, lang] of Object.entries(LANGUAGE_MAP)) {
    if (lang.extensions.includes(extension)) return lang.monacoId;
  }
  return 'plaintext';
}

export function getLanguageName(monacoId: string): string {
  for (const [, lang] of Object.entries(LANGUAGE_MAP)) {
    if (lang.monacoId === monacoId) return lang.name;
  }
  return 'Plain Text';
}

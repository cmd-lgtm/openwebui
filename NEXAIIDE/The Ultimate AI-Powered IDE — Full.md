# &nbsp;The Ultimate AI-Powered IDE — Full System Architecture Prompt

### &nbsp; MASTER PROMPT

#### &nbsp;You are an elite software architect and full-stack engineer. Build me a complete,

#### production-grade AI-Powered IDE (code name: "NEXUS IDE") from scratch — a desktop

#### application that rivals Google's Project IDX/Antigravity, Kiro, Cursor, and Windsurf.

#### 

#### This IDE must be a fully autonomous development environment with multi-agent AI

#### orchestration, integrated terminal, file system management, local database support,

#### VS Code compatibility, and support for both cloud and local AI models.

#### 

#### Below is the COMPLETE specification. Build every module, every file, every config.

### 📁 PROJECT STRUCTURE

nexus-ide/

├── package.json

├── electron-builder.yml

├── tsconfig.json

├── .env.example

├── docker-compose.yml

│

├── src/

│   ├── main/                          # Electron Main Process

│   │   ├── index.ts                   # App entry point

│   │   ├── window-manager.ts          # Window lifecycle

│   │   ├── ipc-handlers.ts           # IPC communication bridge

│   │   ├── app-updater.ts            # Auto-update system

│   │   ├── native-menu.ts            # Native OS menus

│   │   └── protocol-handler.ts       # Custom protocol (nexus://)

│   │

│   ├── renderer/                      # Frontend (React + Monaco)

│   │   ├── App.tsx

│   │   ├── index.html

│   │   ├── styles/

│   │   │   ├── global.css

│   │   │   ├── themes/

│   │   │   │   ├── dark-nexus.css

│   │   │   │   ├── light-nexus.css

│   │   │   │   ├── cyberpunk.css

│   │   │   │   └── solarized.css

│   │   │   └── components/

│   │   │

│   │   ├── components/

│   │   │   ├── Editor/

│   │   │   │   ├── MonacoEditor.tsx        # Core code editor

│   │   │   │   ├── EditorTabs.tsx          # Multi-tab system

│   │   │   │   ├── MiniMap.tsx             # Code minimap

│   │   │   │   ├── BreadCrumb.tsx          # File path breadcrumb

│   │   │   │   ├── DiffViewer.tsx          # Git diff viewer

│   │   │   │   ├── InlineCompletion.tsx    # AI autocomplete overlay

│   │   │   │   ├── CodeLens.tsx            # AI-powered code lens

│   │   │   │   └── CollaborativeCursor.tsx # Multi-cursor support

│   │   │   │

│   │   │   ├── Terminal/

│   │   │   │   ├── TerminalPanel.tsx       # Integrated terminal

│   │   │   │   ├── TerminalTabs.tsx        # Multiple terminal instances

│   │   │   │   ├── TerminalManager.ts      # PTY process management

│   │   │   │   ├── ShellSelector.tsx       # bash/zsh/powershell/fish

│   │   │   │   └── CommandPalette.tsx      # AI-suggested commands

│   │   │   │

│   │   │   ├── FileExplorer/

│   │   │   │   ├── FileTree.tsx            # File system tree

│   │   │   │   ├── FileTreeNode.tsx        # Individual tree node

│   │   │   │   ├── FileWatcher.ts          # Real-time file watching

│   │   │   │   ├── FileOperations.ts       # CRUD operations

│   │   │   │   ├── SearchFiles.tsx         # Fuzzy file search

│   │   │   │   ├── GitStatus.tsx           # Git status indicators

│   │   │   │   └── DragDrop.tsx            # Drag and drop support

│   │   │   │

│   │   │   ├── AIPanel/

│   │   │   │   ├── ChatInterface.tsx       # Main AI chat panel

│   │   │   │   ├── AgentOrchestrator.tsx   # Multi-agent dashboard

│   │   │   │   ├── AgentCard.tsx           # Individual agent status

│   │   │   │   ├── ContextWindow.tsx       # Context management UI

│   │   │   │   ├── ModelSelector.tsx       # AI model picker

│   │   │   │   ├── PromptTemplates.tsx     # Saved prompt templates

│   │   │   │   ├── CodeReview.tsx          # AI code review panel

│   │   │   │   ├── AgentWorkflow.tsx       # Visual workflow builder

│   │   │   │   └── StreamRenderer.tsx      # Streaming response renderer

│   │   │   │

│   │   │   ├── Database/

│   │   │   │   ├── DatabaseExplorer.tsx    # DB browser panel

│   │   │   │   ├── QueryEditor.tsx         # SQL/NoSQL query editor

│   │   │   │   ├── TableViewer.tsx         # Data table viewer

│   │   │   │   ├── SchemaVisualizer.tsx    # ER diagram viewer

│   │   │   │   ├── ConnectionManager.tsx   # DB connection manager

│   │   │   │   └── QueryHistory.tsx        # Query history

│   │   │   │

│   │   │   ├── Git/

│   │   │   │   ├── GitPanel.tsx            # Source control panel

│   │   │   │   ├── CommitHistory.tsx       # Commit log viewer

│   │   │   │   ├── BranchManager.tsx       # Branch operations

│   │   │   │   ├── MergeConflict.tsx       # Conflict resolver

│   │   │   │   ├── GitGraph.tsx            # Visual git graph

│   │   │   │   └── PRCreator.tsx           # Pull request creator

│   │   │   │

│   │   │   ├── Extensions/

│   │   │   │   ├── ExtensionMarketplace.tsx  # Extension store

│   │   │   │   ├── ExtensionManager.tsx      # Installed extensions

│   │   │   │   ├── ExtensionHost.ts          # Extension runtime

│   │   │   │   └── VSCodeCompatLayer.ts      # VSCode extension compat

│   │   │   │

│   │   │   ├── Layout/

│   │   │   │   ├── MainLayout.tsx          # App layout container

│   │   │   │   ├── Sidebar.tsx             # Left sidebar

│   │   │   │   ├── ActivityBar.tsx         # Activity bar (icons)

│   │   │   │   ├── StatusBar.tsx           # Bottom status bar

│   │   │   │   ├── PanelContainer.tsx      # Bottom panel container

│   │   │   │   ├── SplitPane.tsx           # Resizable split panes

│   │   │   │   └── CommandCenter.tsx       # Ctrl+Shift+P command palette

│   │   │   │

│   │   │   ├── Preview/

│   │   │   │   ├── WebPreview.tsx          # Live web preview

│   │   │   │   ├── MarkdownPreview.tsx     # Markdown renderer

│   │   │   │   ├── APITester.tsx           # REST/GraphQL tester

│   │   │   │   └── ImagePreview.tsx        # Image viewer

│   │   │   │

│   │   │   └── Settings/

│   │   │       ├── SettingsPanel.tsx        # Settings UI

│   │   │       ├── KeybindingEditor.tsx     # Keyboard shortcuts

│   │   │       ├── ThemeSelector.tsx        # Theme management

│   │   │       └── AIConfiguration.tsx      # AI model settings

│   │   │

│   │   ├── hooks/

│   │   │   ├── useAI.ts                    # AI interaction hook

│   │   │   ├── useFileSystem.ts            # File system hook

│   │   │   ├── useTerminal.ts              # Terminal hook

│   │   │   ├── useDatabase.ts              # Database hook

│   │   │   ├── useGit.ts                   # Git operations hook

│   │   │   ├── useWebSocket.ts             # WebSocket hook

│   │   │   ├── useEditor.ts                # Editor state hook

│   │   │   └── useTheme.ts                 # Theme hook

│   │   │

│   │   └── store/

│   │       ├── index.ts                    # Zustand store root

│   │       ├── editorStore.ts              # Editor state

│   │       ├── fileStore.ts                # File system state

│   │       ├── aiStore.ts                  # AI/Agent state

│   │       ├── terminalStore.ts            # Terminal state

│   │       ├── databaseStore.ts            # Database state

│   │       ├── gitStore.ts                 # Git state

│   │       └── settingsStore.ts            # Settings state

│   │

│   ├── backend/                           # Backend Server

│   │   ├── server.ts                      # Express/Fastify server

│   │   ├── websocket.ts                   # WebSocket server

│   │   │

│   │   ├── ai/                            # AI Engine Core

│   │   │   ├── engine.ts                  # Main AI engine orchestrator

│   │   │   ├── context-manager.ts         # Context window management

│   │   │   ├── token-counter.ts           # Token counting utility

│   │   │   ├── prompt-builder.ts          # Dynamic prompt construction

│   │   │   ├── response-parser.ts         # AI response parsing

│   │   │   ├── cache-manager.ts           # Response caching (Redis)

│   │   │   ├── rate-limiter.ts            # API rate limiting

│   │   │   ├── cost-tracker.ts            # API cost tracking

│   │   │   │

│   │   │   ├── providers/                 # AI Model Providers

│   │   │   │   ├── base-provider.ts       # Abstract provider interface

│   │   │   │   ├── openai.ts              # OpenAI GPT-4/4o/o1/o3

│   │   │   │   ├── anthropic.ts           # Claude 3.5/4 Sonnet/Opus

│   │   │   │   ├── google.ts              # Gemini 2.5 Pro/Flash

│   │   │   │   ├── deepseek.ts            # DeepSeek V3/R1

│   │   │   │   ├── mistral.ts             # Mistral/Codestral

│   │   │   │   ├── groq.ts                # Groq (ultra-fast inference)

│   │   │   │   ├── together.ts            # Together AI

│   │   │   │   ├── openrouter.ts          # OpenRouter (multi-model)

│   │   │   │   ├── cohere.ts              # Cohere Command R+

│   │   │   │   ├── xai.ts                 # xAI Grok

│   │   │   │   ├── aws-bedrock.ts         # AWS Bedrock

│   │   │   │   ├── azure-openai.ts        # Azure OpenAI

│   │   │   │   │

│   │   │   │   ├── local/                 # Local AI Providers

│   │   │   │   │   ├── ollama.ts          # Ollama integration

│   │   │   │   │   ├── lmstudio.ts        # LM Studio integration

│   │   │   │   │   ├── llamacpp.ts        # llama.cpp direct

│   │   │   │   │   ├── vllm.ts            # vLLM server

│   │   │   │   │   ├── localai.ts         # LocalAI integration

│   │   │   │   │   ├── jan.ts             # Jan AI integration

│   │   │   │   │   └── koboldcpp.ts       # KoboldCpp integration

│   │   │   │   │

│   │   │   │   └── coding-tools/          # Coding-Specific AI Tools

│   │   │   │       ├── opencode.ts        # OpenCode integration

│   │   │   │       ├── aider.ts           # Aider integration

│   │   │   │       ├── continue.ts        # Continue.dev integration

│   │   │   │       ├── tabby.ts           # Tabby (self-hosted Copilot)

│   │   │   │       ├── codeium.ts         # Codeium integration

│   │   │   │       └── supermaven.ts      # Supermaven integration

│   │   │   │

│   │   │   ├── agents/                    # Multi-Agent System

│   │   │   │   ├── agent-manager.ts       # Agent lifecycle manager

│   │   │   │   ├── agent-registry.ts      # Agent registration system

│   │   │   │   ├── agent-communication.ts # Inter-agent messaging

│   │   │   │   ├── task-queue.ts          # Agent task queue (BullMQ)

│   │   │   │   ├── memory-store.ts        # Agent memory (vector DB)

│   │   │   │   │

│   │   │   │   ├── specialized/           # Specialized Agents

│   │   │   │   │   ├── architect-agent.ts      # System design agent

│   │   │   │   │   ├── coder-agent.ts          # Code generation agent

│   │   │   │   │   ├── reviewer-agent.ts       # Code review agent

│   │   │   │   │   ├── debugger-agent.ts       # Bug finding agent

│   │   │   │   │   ├── tester-agent.ts         # Test generation agent

│   │   │   │   │   ├── refactor-agent.ts       # Refactoring agent

│   │   │   │   │   ├── docs-agent.ts           # Documentation agent

│   │   │   │   │   ├── security-agent.ts       # Security audit agent

│   │   │   │   │   ├── devops-agent.ts         # DevOps/CI-CD agent

│   │   │   │   │   ├── database-agent.ts       # Database design agent

│   │   │   │   │   ├── ui-agent.ts             # UI/UX design agent

│   │   │   │   │   ├── performance-agent.ts    # Performance optimization

│   │   │   │   │   ├── api-agent.ts            # API design agent

│   │   │   │   │   ├── terminal-agent.ts       # Terminal command agent

│   │   │   │   │   └── research-agent.ts       # Web research agent

│   │   │   │   │

│   │   │   │   ├── workflows/             # Agent Workflow Patterns

│   │   │   │   │   ├── sequential.ts      # Sequential execution

│   │   │   │   │   ├── parallel.ts        # Parallel execution

│   │   │   │   │   ├── hierarchical.ts    # Manager-worker pattern

│   │   │   │   │   ├── consensus.ts       # Multi-agent consensus

│   │   │   │   │   ├── debate.ts          # Agent debate pattern

│   │   │   │   │   └── swarm.ts           # Swarm intelligence

│   │   │   │   │

│   │   │   │   └── tools/                 # Agent Tools

│   │   │   │       ├── file-tool.ts       # File read/write/search

│   │   │   │       ├── terminal-tool.ts   # Execute commands

│   │   │   │       ├── browser-tool.ts    # Web browsing/scraping

│   │   │   │       ├── search-tool.ts     # Code search (ripgrep)

│   │   │   │       ├── git-tool.ts        # Git operations

│   │   │   │       ├── database-tool.ts   # Database queries

│   │   │   │       ├── api-tool.ts        # HTTP requests

│   │   │   │       ├── linter-tool.ts     # Code linting

│   │   │   │       ├── test-runner-tool.ts # Run tests

│   │   │   │       └── docker-tool.ts     # Docker operations

│   │   │   │

│   │   │   └── embeddings/               # Vector Embeddings

│   │   │       ├── embedding-engine.ts    # Embedding generation

│   │   │       ├── code-indexer.ts        # Codebase indexing

│   │   │       ├── semantic-search.ts     # Semantic code search

│   │   │       └── rag-pipeline.ts        # RAG for codebase

│   │   │

│   │   ├── terminal/                      # Terminal Backend

│   │   │   ├── pty-manager.ts             # PTY process manager

│   │   │   ├── shell-integration.ts       # Shell integration scripts

│   │   │   ├── command-history.ts         # Command history DB

│   │   │   ├── environment-manager.ts     # ENV variable manager

│   │   │   └── session-manager.ts         # Terminal session persistence

│   │   │

│   │   ├── filesystem/                    # File System Backend

│   │   │   ├── fs-manager.ts              # File system operations

│   │   │   ├── watcher.ts                 # File watcher (chokidar)

│   │   │   ├── search.ts                  # File search (ripgrep)

│   │   │   ├── workspace.ts              # Workspace management

│   │   │   └── temp-files.ts             # Temp file management

│   │   │

│   │   ├── database/                      # Database Backend

│   │   │   ├── db-manager.ts              # Database connection manager

│   │   │   ├── drivers/

│   │   │   │   ├── sqlite.ts              # SQLite driver

│   │   │   │   ├── postgresql.ts          # PostgreSQL driver

│   │   │   │   ├── mysql.ts               # MySQL driver

│   │   │   │   ├── mongodb.ts             # MongoDB driver

│   │   │   │   ├── redis.ts               # Redis driver

│   │   │   │   └── duckdb.ts              # DuckDB driver

│   │   │   ├── query-executor.ts          # Safe query execution

│   │   │   ├── schema-introspector.ts     # Schema discovery

│   │   │   └── migration-manager.ts       # DB migrations

│   │   │

│   │   ├── git/                           # Git Backend

│   │   │   ├── git-manager.ts             # Git operations (isomorphic-git)

│   │   │   ├── diff-engine.ts             # Diff computation

│   │   │   ├── merge-engine.ts            # Merge conflict resolution

│   │   │   └── github-api.ts              # GitHub/GitLab API

│   │   │

│   │   ├── lsp/                           # Language Server Protocol

│   │   │   ├── lsp-manager.ts             # LSP client manager

│   │   │   ├── servers/

│   │   │   │   ├── typescript.ts          # TypeScript LSP

│   │   │   │   ├── python.ts              # Python (Pyright/Pylsp)

│   │   │   │   ├── rust.ts                # Rust (rust-analyzer)

│   │   │   │   ├── go.ts                  # Go (gopls)

│   │   │   │   ├── java.ts               # Java (Eclipse JDT)

│   │   │   │   ├── cpp.ts                # C/C++ (clangd)

│   │   │   │   └── web.ts                # HTML/CSS/JSON

│   │   │   └── diagnostics.ts            # Diagnostic aggregator

│   │   │

│   │   ├── extensions/                    # Extension System

│   │   │   ├── extension-host.ts          # Sandboxed extension runtime

│   │   │   ├── extension-api.ts           # Extension API surface

│   │   │   ├── marketplace-client.ts      # Extension marketplace

│   │   │   ├── vscode-compat.ts           # VSCode API compatibility

│   │   │   └── extension-loader.ts        # Extension loading/activation

│   │   │

│   │   └── security/                      # Security Layer

│   │       ├── sandbox.ts                 # Process sandboxing

│   │       ├── permission-manager.ts      # Permission system

│   │       ├── secret-store.ts            # Encrypted secret storage

│   │       └── audit-log.ts               # Security audit logging

│   │

│   ├── shared/                            # Shared Types \& Utilities

│   │   ├── types/

│   │   │   ├── ai.types.ts

│   │   │   ├── agent.types.ts

│   │   │   ├── editor.types.ts

│   │   │   ├── terminal.types.ts

│   │   │   ├── filesystem.types.ts

│   │   │   ├── database.types.ts

│   │   │   ├── git.types.ts

│   │   │   ├── extension.types.ts

│   │   │   └── settings.types.ts

│   │   │

│   │   ├── constants/

│   │   │   ├── ai-models.ts               # All supported AI models

│   │   │   ├── languages.ts               # Supported languages

│   │   │   ├── keybindings.ts             # Default keybindings

│   │   │   └── defaults.ts                # Default settings

│   │   │

│   │   └── utils/

│   │       ├── logger.ts                  # Winston logger

│   │       ├── crypto.ts                  # Encryption utilities

│   │       ├── debounce.ts

│   │       ├── event-emitter.ts

│   │       └── validators.ts

│   │

│   └── workers/                           # Web Workers

│       ├── ai-worker.ts                   # AI processing worker

│       ├── indexing-worker.ts             # File indexing worker

│       ├── search-worker.ts               # Search worker

│       └── syntax-worker.ts               # Syntax highlighting worker

│

├── extensions/                            # Built-in Extensions

│   ├── nexus-theme/

│   ├── nexus-icons/

│   ├── nexus-git-lens/

│   ├── nexus-docker/

│   ├── nexus-prettier/

│   ├── nexus-eslint/

│   └── nexus-ai-snippets/

│

├── scripts/

│   ├── build.ts

│   ├── dev.ts

│   ├── package.ts

│   └── setup-local-ai.sh                 # Ollama/LM Studio/OpenCode setup And Also Setup option from cmd command

│

├── tests/

│   ├── unit/

│   ├── integration/

│   └── e2e/

│

└── docs/

&nbsp;   ├── architecture.md

&nbsp;   ├── ai-providers.md

&nbsp;   ├── extension-api.md

&nbsp;   └── contributing.md

### CORE IMPLEMENTATION FILES

### 1\. Package.json

{

&nbsp; "name": "nexus-ide",

&nbsp; "version": "1.0.0",

&nbsp; "description": "AI-Powered IDE with Multi-Agent Orchestration",

&nbsp; "main": "dist/main/index.js",

&nbsp; "scripts": {

&nbsp;   "dev": "concurrently \\"npm run dev:main\\" \\"npm run dev:renderer\\" \\"npm run dev:backend\\"",

&nbsp;   "dev:main": "electron-vite dev",

&nbsp;   "dev:renderer": "vite dev",

&nbsp;   "dev:backend": "tsx watch src/backend/server.ts",

&nbsp;   "build": "electron-vite build \&\& electron-builder",

&nbsp;   "build:mac": "electron-builder --mac",

&nbsp;   "build:win": "electron-builder --win",

&nbsp;   "build:linux": "electron-builder --linux",

&nbsp;   "test": "vitest",

&nbsp;   "test:e2e": "playwright test",

&nbsp;   "lint": "eslint src/",

&nbsp;   "typecheck": "tsc --noEmit"

&nbsp; },

&nbsp; "dependencies": {

&nbsp;   "electron": "^31.0.0",

&nbsp;   "electron-vite": "^2.3.0",



&nbsp;   "react": "^18.3.0",

&nbsp;   "react-dom": "^18.3.0",

&nbsp;   "zustand": "^4.5.0",

&nbsp;   "react-query": "^5.0.0",



&nbsp;   "monaco-editor": "^0.50.0",

&nbsp;   "@monaco-editor/react": "^4.6.0",



&nbsp;   "@xterm/xterm": "^5.5.0",

&nbsp;   "@xterm/addon-fit": "^0.10.0",

&nbsp;   "@xterm/addon-webgl": "^0.18.0",

&nbsp;   "@xterm/addon-search": "^0.15.0",

&nbsp;   "@xterm/addon-web-links": "^0.11.0",

&nbsp;   "node-pty": "^1.0.0",



&nbsp;   "chokidar": "^3.6.0",

&nbsp;   "@vscode/ripgrep": "^1.15.0",



&nbsp;   "isomorphic-git": "^1.25.0",



&nbsp;   "better-sqlite3": "^11.0.0",

&nbsp;   "pg": "^8.12.0",

&nbsp;   "mysql2": "^3.10.0",

&nbsp;   "mongodb": "^6.7.0",

&nbsp;   "ioredis": "^5.4.0",

&nbsp;   "duckdb": "^0.10.0",



&nbsp;   "openai": "^4.52.0",

&nbsp;   "@anthropic-ai/sdk": "^0.24.0",

&nbsp;   "@google/generative-ai": "^0.14.0",

&nbsp;   "ollama": "^0.5.0",

&nbsp;   "cohere-ai": "^7.10.0",



&nbsp;   "@langchain/core": "^0.2.0",

&nbsp;   "@langchain/community": "^0.2.0",

&nbsp;   "langchain": "^0.2.0",



&nbsp;   "chromadb": "^1.8.0",

&nbsp;   "faiss-node": "^0.5.0",



&nbsp;   "bullmq": "^5.8.0",



&nbsp;   "express": "^4.19.0",

&nbsp;   "ws": "^8.17.0",

&nbsp;   "socket.io": "^4.7.0",



&nbsp;   "vscode-languageclient": "^9.0.0",

&nbsp;   "vscode-languageserver": "^9.0.0",

&nbsp;   "vscode-languageserver-protocol": "^3.17.0",



&nbsp;   "winston": "^3.13.0",

&nbsp;   "keytar": "^7.9.0",

&nbsp;   "electron-store": "^9.0.0",

&nbsp;   "electron-updater": "^6.2.0",



&nbsp;   "tree-sitter": "^0.21.0",

&nbsp;   "tree-sitter-javascript": "^0.21.0",

&nbsp;   "tree-sitter-typescript": "^0.21.0",

&nbsp;   "tree-sitter-python": "^0.21.0",

&nbsp;   "tree-sitter-rust": "^0.21.0",



&nbsp;   "dockerode": "^4.0.0",



&nbsp;   "@radix-ui/react-dialog": "^1.1.0",

&nbsp;   "@radix-ui/react-dropdown-menu": "^2.1.0",

&nbsp;   "@radix-ui/react-tabs": "^1.1.0",

&nbsp;   "@radix-ui/react-tooltip": "^1.1.0",

&nbsp;   "lucide-react": "^0.400.0",

&nbsp;   "tailwindcss": "^3.4.0",

&nbsp;   "framer-motion": "^11.2.0",

&nbsp;   "react-resizable-panels": "^2.0.0",

&nbsp;   "cmdk": "^1.0.0",

&nbsp;   "sonner": "^1.5.0"

&nbsp; },

&nbsp; "devDependencies": {

&nbsp;   "typescript": "^5.5.0",

&nbsp;   "vite": "^5.3.0",

&nbsp;   "@types/react": "^18.3.0",

&nbsp;   "vitest": "^1.6.0",

&nbsp;   "playwright": "^1.45.0",

&nbsp;   "eslint": "^9.6.0",

&nbsp;   "prettier": "^3.3.0",

&nbsp;   "electron-builder": "^24.13.0"

&nbsp; }

}





### 2\. Electron Main Entry (src/main/index.ts)

import { app, BrowserWindow, ipcMain, protocol, Menu } from 'electron';

import path from 'path';

import { WindowManager } from './window-manager';

import { registerIpcHandlers } from './ipc-handlers';

import { createNativeMenu } from './native-menu';

import { setupAutoUpdater } from './app-updater';

import { registerProtocol } from './protocol-handler';



class NexusIDE {

&nbsp; private windowManager: WindowManager;



&nbsp; constructor() {

&nbsp;   this.windowManager = new WindowManager();

&nbsp;   this.initialize();

&nbsp; }



&nbsp; private async initialize() {

&nbsp;   await app.whenReady();



&nbsp;   // Register custom protocol

&nbsp;   registerProtocol();



&nbsp;   // Create native menu

&nbsp;   Menu.setApplicationMenu(createNativeMenu());



&nbsp;   // Register IPC handlers

&nbsp;   registerIpcHandlers(ipcMain);



&nbsp;   // Create main window

&nbsp;   this.windowManager.createMainWindow();



&nbsp;   // Setup auto-updater

&nbsp;   setupAutoUpdater();



&nbsp;   // Handle app lifecycle

&nbsp;   app.on('window-all-closed', () => {

&nbsp;     if (process.platform !== 'darwin') app.quit();

&nbsp;   });



&nbsp;   app.on('activate', () => {

&nbsp;     if (BrowserWindow.getAllWindows().length === 0) {

&nbsp;       this.windowManager.createMainWindow();

&nbsp;     }

&nbsp;   });



&nbsp;   // Handle second instance

&nbsp;   const gotTheLock = app.requestSingleInstanceLock();

&nbsp;   if (!gotTheLock) {

&nbsp;     app.quit();

&nbsp;   } else {

&nbsp;     app.on('second-instance', (\_event, commandLine) => {

&nbsp;       const win = this.windowManager.getMainWindow();

&nbsp;       if (win) {

&nbsp;         if (win.isMinimized()) win.restore();

&nbsp;         win.focus();

&nbsp;         // Handle file open from command line

&nbsp;         const filePath = commandLine\[commandLine.length - 1];

&nbsp;         if (filePath \&\& !filePath.startsWith('--')) {

&nbsp;           win.webContents.send('open-file', filePath);

&nbsp;         }

&nbsp;       }

&nbsp;     });

&nbsp;   }

&nbsp; }

}



new NexusIDE();



### 3\. Window Manager (src/main/window-manager.ts)

import { BrowserWindow, screen } from 'electron';

import path from 'path';



export class WindowManager {

&nbsp; private mainWindow: BrowserWindow | null = null;

&nbsp; private windows: Map<string, BrowserWindow> = new Map();



&nbsp; createMainWindow(): BrowserWindow {

&nbsp;   const { width, height } = screen.getPrimaryDisplay().workAreaSize;



&nbsp;   this.mainWindow = new BrowserWindow({

&nbsp;     width: Math.min(1920, width),

&nbsp;     height: Math.min(1080, height),

&nbsp;     minWidth: 1024,

&nbsp;     minHeight: 768,

&nbsp;     title: 'Nexus IDE',

&nbsp;     titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',

&nbsp;     trafficLightPosition: { x: 15, y: 10 },

&nbsp;     backgroundColor: '#0d1117',

&nbsp;     show: false,

&nbsp;     webPreferences: {

&nbsp;       preload: path.join(\_\_dirname, '../preload/index.js'),

&nbsp;       nodeIntegration: false,

&nbsp;       contextIsolation: true,

&nbsp;       sandbox: false, // Required for node-pty

&nbsp;       webviewTag: true,

&nbsp;       spellcheck: true,

&nbsp;     },

&nbsp;   });



&nbsp;   // Load renderer

&nbsp;   if (process.env.NODE\_ENV === 'development') {

&nbsp;     this.mainWindow.loadURL('http://localhost:5173');

&nbsp;     this.mainWindow.webContents.openDevTools();

&nbsp;   } else {

&nbsp;     this.mainWindow.loadFile(

&nbsp;       path.join(\_\_dirname, '../renderer/index.html')

&nbsp;     );

&nbsp;   }



&nbsp;   this.mainWindow.once('ready-to-show', () => {

&nbsp;     this.mainWindow?.show();

&nbsp;     this.mainWindow?.focus();

&nbsp;   });



&nbsp;   this.mainWindow.on('closed', () => {

&nbsp;     this.mainWindow = null;

&nbsp;   });



&nbsp;   return this.mainWindow;

&nbsp; }



&nbsp; getMainWindow(): BrowserWindow | null {

&nbsp;   return this.mainWindow;

&nbsp; }



&nbsp; createChildWindow(id: string, options: Partial<Electron.BrowserWindowConstructorOptions> = {}): BrowserWindow {

&nbsp;   const child = new BrowserWindow({

&nbsp;     width: 800,

&nbsp;     height: 600,

&nbsp;     parent: this.mainWindow || undefined,

&nbsp;     webPreferences: {

&nbsp;       preload: path.join(\_\_dirname, '../preload/index.js'),

&nbsp;       contextIsolation: true,

&nbsp;       nodeIntegration: false,

&nbsp;     },

&nbsp;     ...options,

&nbsp;   });



&nbsp;   this.windows.set(id, child);

&nbsp;   child.on('closed', () => this.windows.delete(id));



&nbsp;   return child;

&nbsp; }

}

### 

### 4\. IPC Handlers (src/main/ipc-handlers.ts)

import { IpcMain, dialog, shell, clipboard } from 'electron';

import { PtyManager } from '../backend/terminal/pty-manager';

import { FSManager } from '../backend/filesystem/fs-manager';

import { GitManager } from '../backend/git/git-manager';

import { DatabaseManager } from '../backend/database/db-manager';



export function registerIpcHandlers(ipcMain: IpcMain) {

&nbsp; const ptyManager = new PtyManager();

&nbsp; const fsManager = new FSManager();

&nbsp; const gitManager = new GitManager();

&nbsp; const dbManager = new DatabaseManager();



&nbsp; // ===== FILE SYSTEM =====

&nbsp; ipcMain.handle('fs:readDir', async (\_, dirPath: string) => {

&nbsp;   return fsManager.readDirectory(dirPath);

&nbsp; });



&nbsp; ipcMain.handle('fs:readFile', async (\_, filePath: string) => {

&nbsp;   return fsManager.readFile(filePath);

&nbsp; });



&nbsp; ipcMain.handle('fs:writeFile', async (\_, filePath: string, content: string) => {

&nbsp;   return fsManager.writeFile(filePath, content);

&nbsp; });



&nbsp; ipcMain.handle('fs:createFile', async (\_, filePath: string) => {

&nbsp;   return fsManager.createFile(filePath);

&nbsp; });



&nbsp; ipcMain.handle('fs:createDir', async (\_, dirPath: string) => {

&nbsp;   return fsManager.createDirectory(dirPath);

&nbsp; });



&nbsp; ipcMain.handle('fs:delete', async (\_, targetPath: string) => {

&nbsp;   return fsManager.delete(targetPath);

&nbsp; });



&nbsp; ipcMain.handle('fs:rename', async (\_, oldPath: string, newPath: string) => {

&nbsp;   return fsManager.rename(oldPath, newPath);

&nbsp; });



&nbsp; ipcMain.handle('fs:search', async (\_, query: string, rootPath: string) => {

&nbsp;   return fsManager.searchFiles(query, rootPath);

&nbsp; });



&nbsp; ipcMain.handle('fs:openFolder', async () => {

&nbsp;   const result = await dialog.showOpenDialog({

&nbsp;     properties: \['openDirectory'],

&nbsp;   });

&nbsp;   return result.canceled ? null : result.filePaths\[0];

&nbsp; });



&nbsp; ipcMain.handle('fs:openFile', async () => {

&nbsp;   const result = await dialog.showOpenDialog({

&nbsp;     properties: \['openFile'],

&nbsp;   });

&nbsp;   return result.canceled ? null : result.filePaths\[0];

&nbsp; });



&nbsp; ipcMain.handle('fs:saveDialog', async (\_, defaultPath?: string) => {

&nbsp;   const result = await dialog.showSaveDialog({

&nbsp;     defaultPath,

&nbsp;   });

&nbsp;   return result.canceled ? null : result.filePath;

&nbsp; });



&nbsp; // ===== TERMINAL =====

&nbsp; ipcMain.handle('terminal:create', async (event, options) => {

&nbsp;   const id = ptyManager.createTerminal(options);



&nbsp;   ptyManager.onData(id, (data) => {

&nbsp;     event.sender.send(`terminal:data:${id}`, data);

&nbsp;   });



&nbsp;   ptyManager.onExit(id, (exitCode) => {

&nbsp;     event.sender.send(`terminal:exit:${id}`, exitCode);

&nbsp;   });



&nbsp;   return id;

&nbsp; });



&nbsp; ipcMain.handle('terminal:write', async (\_, id: string, data: string) => {

&nbsp;   ptyManager.write(id, data);

&nbsp; });



&nbsp; ipcMain.handle('terminal:resize', async (\_, id: string, cols: number, rows: number) => {

&nbsp;   ptyManager.resize(id, cols, rows);

&nbsp; });



&nbsp; ipcMain.handle('terminal:kill', async (\_, id: string) => {

&nbsp;   ptyManager.kill(id);

&nbsp; });



&nbsp; ipcMain.handle('terminal:getShells', async () => {

&nbsp;   return ptyManager.getAvailableShells();

&nbsp; });



&nbsp; // ===== GIT =====

&nbsp; ipcMain.handle('git:status', async (\_, repoPath: string) => {

&nbsp;   return gitManager.getStatus(repoPath);

&nbsp; });



&nbsp; ipcMain.handle('git:log', async (\_, repoPath: string, limit?: number) => {

&nbsp;   return gitManager.getLog(repoPath, limit);

&nbsp; });



&nbsp; ipcMain.handle('git:commit', async (\_, repoPath: string, message: string) => {

&nbsp;   return gitManager.commit(repoPath, message);

&nbsp; });



&nbsp; ipcMain.handle('git:push', async (\_, repoPath: string) => {

&nbsp;   return gitManager.push(repoPath);

&nbsp; });



&nbsp; ipcMain.handle('git:pull', async (\_, repoPath: string) => {

&nbsp;   return gitManager.pull(repoPath);

&nbsp; });



&nbsp; ipcMain.handle('git:branch', async (\_, repoPath: string) => {

&nbsp;   return gitManager.getBranches(repoPath);

&nbsp; });



&nbsp; ipcMain.handle('git:checkout', async (\_, repoPath: string, branch: string) => {

&nbsp;   return gitManager.checkout(repoPath, branch);

&nbsp; });



&nbsp; ipcMain.handle('git:diff', async (\_, repoPath: string, filePath?: string) => {

&nbsp;   return gitManager.getDiff(repoPath, filePath);

&nbsp; });



&nbsp; // ===== DATABASE =====

&nbsp; ipcMain.handle('db:connect', async (\_, config) => {

&nbsp;   return dbManager.connect(config);

&nbsp; });



&nbsp; ipcMain.handle('db:disconnect', async (\_, connectionId: string) => {

&nbsp;   return dbManager.disconnect(connectionId);

&nbsp; });



&nbsp; ipcMain.handle('db:query', async (\_, connectionId: string, query: string) => {

&nbsp;   return dbManager.executeQuery(connectionId, query);

&nbsp; });



&nbsp; ipcMain.handle('db:getTables', async (\_, connectionId: string) => {

&nbsp;   return dbManager.getTables(connectionId);

&nbsp; });



&nbsp; ipcMain.handle('db:getSchema', async (\_, connectionId: string, table: string) => {

&nbsp;   return dbManager.getTableSchema(connectionId, table);

&nbsp; });



&nbsp; // ===== SHELL =====

&nbsp; ipcMain.handle('shell:openExternal', async (\_, url: string) => {

&nbsp;   return shell.openExternal(url);

&nbsp; });



&nbsp; ipcMain.handle('shell:showItemInFolder', async (\_, filePath: string) => {

&nbsp;   shell.showItemInFolder(filePath);

&nbsp; });



&nbsp; // ===== CLIPBOARD =====

&nbsp; ipcMain.handle('clipboard:read', async () => {

&nbsp;   return clipboard.readText();

&nbsp; });



&nbsp; ipcMain.handle('clipboard:write', async (\_, text: string) => {

&nbsp;   clipboard.writeText(text);

&nbsp; });

}

### 5\. AI Engine Core (src/backend/ai/engine.ts)



import { EventEmitter } from 'events';

import { BaseProvider } from './providers/base-provider';

import { OpenAIProvider } from './providers/openai';

import { AnthropicProvider } from './providers/anthropic';

import { GoogleProvider } from './providers/google';

import { OllamaProvider } from './providers/local/ollama';

import { LMStudioProvider } from './providers/local/lmstudio';

import { DeepSeekProvider } from './providers/deepseek';

import { GroqProvider } from './providers/groq';

import { OpenRouterProvider } from './providers/openrouter';

import { ContextManager } from './context-manager';

import { TokenCounter } from './token-counter';

import { PromptBuilder } from './prompt-builder';

import { CacheManager } from './cache-manager';

import { CostTracker } from './cost-tracker';

import {

&nbsp; AIRequest,

&nbsp; AIResponse,

&nbsp; AIStreamCallback,

&nbsp; ModelConfig,

&nbsp; ProviderType,

} from '../../shared/types/ai.types';



export class AIEngine extends EventEmitter {

&nbsp; private providers: Map<ProviderType, BaseProvider> = new Map();

&nbsp; private contextManager: ContextManager;

&nbsp; private tokenCounter: TokenCounter;

&nbsp; private promptBuilder: PromptBuilder;

&nbsp; private cacheManager: CacheManager;

&nbsp; private costTracker: CostTracker;

&nbsp; private activeModel: ModelConfig;



&nbsp; constructor() {

&nbsp;   super();

&nbsp;   this.contextManager = new ContextManager();

&nbsp;   this.tokenCounter = new TokenCounter();

&nbsp;   this.promptBuilder = new PromptBuilder();

&nbsp;   this.cacheManager = new CacheManager();

&nbsp;   this.costTracker = new CostTracker();

&nbsp;   this.activeModel = this.getDefaultModel();

&nbsp;   this.initializeProviders();

&nbsp; }



&nbsp; private initializeProviders() {

&nbsp;   // Cloud Providers

&nbsp;   this.registerProvider('openai', new OpenAIProvider());

&nbsp;   this.registerProvider('anthropic', new AnthropicProvider());

&nbsp;   this.registerProvider('google', new GoogleProvider());

&nbsp;   this.registerProvider('deepseek', new DeepSeekProvider());

&nbsp;   this.registerProvider('groq', new GroqProvider());

&nbsp;   this.registerProvider('openrouter', new OpenRouterProvider());



&nbsp;   // Local Providers

&nbsp;   this.registerProvider('ollama', new OllamaProvider());

&nbsp;   this.registerProvider('lmstudio', new LMStudioProvider());

&nbsp; }



&nbsp; registerProvider(type: ProviderType, provider: BaseProvider) {

&nbsp;   this.providers.set(type, provider);

&nbsp;   this.emit('provider:registered', type);

&nbsp; }



&nbsp; getProvider(type: ProviderType): BaseProvider {

&nbsp;   const provider = this.providers.get(type);

&nbsp;   if (!provider) throw new Error(`Provider ${type} not found`);

&nbsp;   return provider;

&nbsp; }



&nbsp; async listAvailableModels(): Promise<ModelConfig\[]> {

&nbsp;   const models: ModelConfig\[] = \[];

&nbsp;   for (const \[type, provider] of this.providers) {

&nbsp;     try {

&nbsp;       const providerModels = await provider.listModels();

&nbsp;       models.push(...providerModels);

&nbsp;     } catch (error) {

&nbsp;       console.warn(`Failed to list models for ${type}:`, error);

&nbsp;     }

&nbsp;   }

&nbsp;   return models;

&nbsp; }



&nbsp; async chat(request: AIRequest): Promise<AIResponse> {

&nbsp;   const provider = this.getProvider(request.model.provider);



&nbsp;   // Build context-aware prompt

&nbsp;   const enrichedMessages = await this.contextManager.enrichMessages(

&nbsp;     request.messages,

&nbsp;     request.context

&nbsp;   );



&nbsp;   // Check cache

&nbsp;   const cacheKey = this.cacheManager.generateKey(enrichedMessages, request.model);

&nbsp;   const cached = await this.cacheManager.get(cacheKey);

&nbsp;   if (cached \&\& !request.skipCache) {

&nbsp;     return cached;

&nbsp;   }



&nbsp;   // Count tokens

&nbsp;   const tokenCount = this.tokenCounter.count(enrichedMessages, request.model);

&nbsp;   this.emit('tokens:counted', tokenCount);



&nbsp;   // Execute request

&nbsp;   const response = await provider.chat({

&nbsp;     ...request,

&nbsp;     messages: enrichedMessages,

&nbsp;   });



&nbsp;   // Track cost

&nbsp;   this.costTracker.track(request.model, response.usage);



&nbsp;   // Cache response

&nbsp;   await this.cacheManager.set(cacheKey, response);



&nbsp;   this.emit('response:complete', response);

&nbsp;   return response;

&nbsp; }



&nbsp; async chatStream(

&nbsp;   request: AIRequest,

&nbsp;   callback: AIStreamCallback

&nbsp; ): Promise<void> {

&nbsp;   const provider = this.getProvider(request.model.provider);



&nbsp;   const enrichedMessages = await this.contextManager.enrichMessages(

&nbsp;     request.messages,

&nbsp;     request.context

&nbsp;   );



&nbsp;   const tokenCount = this.tokenCounter.count(enrichedMessages, request.model);

&nbsp;   this.emit('tokens:counted', tokenCount);



&nbsp;   await provider.chatStream(

&nbsp;     { ...request, messages: enrichedMessages },

&nbsp;     (chunk) => {

&nbsp;       callback(chunk);

&nbsp;       this.emit('stream:chunk', chunk);

&nbsp;     }

&nbsp;   );



&nbsp;   this.emit('stream:complete');

&nbsp; }



&nbsp; async generateCompletion(

&nbsp;   code: string,

&nbsp;   language: string,

&nbsp;   cursorPosition: { line: number; column: number }

&nbsp; ): Promise<string> {

&nbsp;   const prompt = this.promptBuilder.buildCompletionPrompt(

&nbsp;     code,

&nbsp;     language,

&nbsp;     cursorPosition

&nbsp;   );



&nbsp;   const response = await this.chat({

&nbsp;     model: this.activeModel,

&nbsp;     messages: \[{ role: 'user', content: prompt }],

&nbsp;     temperature: 0.1,

&nbsp;     maxTokens: 500,

&nbsp;     context: { type: 'completion' },

&nbsp;   });



&nbsp;   return response.content;

&nbsp; }



&nbsp; async generateCode(

&nbsp;   instruction: string,

&nbsp;   context: {

&nbsp;     currentFile?: string;

&nbsp;     language?: string;

&nbsp;     projectStructure?: string\[];

&nbsp;     relatedFiles?: { path: string; content: string }\[];

&nbsp;   }

&nbsp; ): Promise<string> {

&nbsp;   const prompt = this.promptBuilder.buildCodeGenerationPrompt(

&nbsp;     instruction,

&nbsp;     context

&nbsp;   );



&nbsp;   const response = await this.chat({

&nbsp;     model: this.activeModel,

&nbsp;     messages: \[

&nbsp;       {

&nbsp;         role: 'system',

&nbsp;         content: this.promptBuilder.getSystemPrompt('coder'),

&nbsp;       },

&nbsp;       { role: 'user', content: prompt },

&nbsp;     ],

&nbsp;     temperature: 0.3,

&nbsp;     maxTokens: 4000,

&nbsp;     context: { type: 'generation' },

&nbsp;   });



&nbsp;   return response.content;

&nbsp; }



&nbsp; async reviewCode(

&nbsp;   code: string,

&nbsp;   language: string

&nbsp; ): Promise<{

&nbsp;   issues: Array<{

&nbsp;     severity: 'error' | 'warning' | 'info';

&nbsp;     line: number;

&nbsp;     message: string;

&nbsp;     suggestion: string;

&nbsp;   }>;

&nbsp;   summary: string;

&nbsp;   score: number;

&nbsp; }> {

&nbsp;   const prompt = this.promptBuilder.buildCodeReviewPrompt(code, language);



&nbsp;   const response = await this.chat({

&nbsp;     model: this.activeModel,

&nbsp;     messages: \[

&nbsp;       {

&nbsp;         role: 'system',

&nbsp;         content: this.promptBuilder.getSystemPrompt('reviewer'),

&nbsp;       },

&nbsp;       { role: 'user', content: prompt },

&nbsp;     ],

&nbsp;     temperature: 0.2,

&nbsp;     context: { type: 'review' },

&nbsp;   });



&nbsp;   return JSON.parse(response.content);

&nbsp; }



&nbsp; async explainCode(code: string, language: string): Promise<string> {

&nbsp;   const response = await this.chat({

&nbsp;     model: this.activeModel,

&nbsp;     messages: \[

&nbsp;       {

&nbsp;         role: 'system',

&nbsp;         content: 'You are an expert code explainer. Explain code clearly and concisely.',

&nbsp;       },

&nbsp;       {

&nbsp;         role: 'user',

&nbsp;         content: `Explain this ${language} code:\\n\\n\\`\\`\\`${language}\\n${code}\\n\\`\\`\\``,

&nbsp;       },

&nbsp;     ],

&nbsp;     temperature: 0.3,

&nbsp;     context: { type: 'explain' },

&nbsp;   });



&nbsp;   return response.content;

&nbsp; }



&nbsp; async refactorCode(

&nbsp;   code: string,

&nbsp;   language: string,

&nbsp;   instruction: string

&nbsp; ): Promise<string> {

&nbsp;   const response = await this.chat({

&nbsp;     model: this.activeModel,

&nbsp;     messages: \[

&nbsp;       {

&nbsp;         role: 'system',

&nbsp;         content: this.promptBuilder.getSystemPrompt('refactor'),

&nbsp;       },

&nbsp;       {

&nbsp;         role: 'user',

&nbsp;         content: `Refactor this ${language} code. Instruction: ${instruction}\\n\\n\\`\\`\\`${language}\\n${code}\\n\\`\\`\\``,

&nbsp;       },

&nbsp;     ],

&nbsp;     temperature: 0.2,

&nbsp;     context: { type: 'refactor' },

&nbsp;   });



&nbsp;   return response.content;

&nbsp; }



&nbsp; setActiveModel(model: ModelConfig) {

&nbsp;   this.activeModel = model;

&nbsp;   this.emit('model:changed', model);

&nbsp; }



&nbsp; getActiveModel(): ModelConfig {

&nbsp;   return this.activeModel;

&nbsp; }



&nbsp; private getDefaultModel(): ModelConfig {

&nbsp;   return {

&nbsp;     id: 'claude-sonnet-4-20250514',

&nbsp;     name: 'Claude 3.5 Sonnet',

&nbsp;     provider: 'anthropic',

&nbsp;     maxTokens: 8192,

&nbsp;     contextWindow: 200000,

&nbsp;   };

&nbsp; }



&nbsp; getCostReport() {

&nbsp;   return this.costTracker.getReport();

&nbsp; }

}



export const aiEngine = new AIEngine();

### 

### 6\. Base AI Provider (src/backend/ai/providers/base-provider.ts)



import {

&nbsp; AIRequest,

&nbsp; AIResponse,

&nbsp; AIStreamCallback,

&nbsp; ModelConfig,

} from '../../../shared/types/ai.types';



export abstract class BaseProvider {

&nbsp; protected apiKey: string;

&nbsp; protected baseUrl: string;



&nbsp; constructor(config?: { apiKey?: string; baseUrl?: string }) {

&nbsp;   this.apiKey = config?.apiKey || '';

&nbsp;   this.baseUrl = config?.baseUrl || '';

&nbsp; }



&nbsp; abstract chat(request: AIRequest): Promise<AIResponse>;

&nbsp; abstract chatStream(request: AIRequest, callback: AIStreamCallback): Promise<void>;

&nbsp; abstract listModels(): Promise<ModelConfig\[]>;

&nbsp; abstract validateConnection(): Promise<boolean>;



&nbsp; setApiKey(key: string) {

&nbsp;   this.apiKey = key;

&nbsp; }



&nbsp; setBaseUrl(url: string) {

&nbsp;   this.baseUrl = url;

&nbsp; }



&nbsp; protected formatError(error: unknown): string {

&nbsp;   if (error instanceof Error) return error.message;

&nbsp;   return String(error);

&nbsp; }

}





### **7. Ollama/lmstudio/opencode etc Provider (src/backend/ai/providers/local/ollama.ts)**

**import { Ollama } from 'ollama';**

**import { BaseProvider } from '../base-provider';**

**import {**

  **AIRequest,**

  **AIResponse,**

  **AIStreamCallback,**

  **ModelConfig,**

**} from '../../../../shared/types/ai.types';**



**export class OllamaProvider extends BaseProvider {**

  **private client: Ollama;**



  **constructor(baseUrl: string = 'http://localhost:11434') {**

    **super({ baseUrl });**

    **this.client = new Ollama({ host: baseUrl });**

  **}**



  **async chat(request: AIRequest): Promise<AIResponse> {**

    **const startTime = Date.now();**



    **const response = await this.client.chat({**

      **model: request.model.id,**

      **messages: request.messages.map((m) => ({**

        **role: m.role as 'system' | 'user' | 'assistant',**

        **content: m.content,**

      **})),**

      **options: {**

        **temperature: request.temperature ?? 0.7,**

        **num\_predict: request.maxTokens ?? 4096,**

        **top\_p: request.topP ?? 0.9,**

        **stop: request.stop,**

      **},**

    **});**



    **return {**

      **content: response.message.content,**

      **model: request.model.id,**

      **provider: 'ollama',**

      **usage: {**

        **promptTokens: response.prompt\_eval\_count || 0,**

        **completionTokens: response.eval\_count || 0,**

        **totalTokens: (response.prompt\_eval\_count || 0) + (response.eval\_count || 0),**

      **},**

      **latency: Date.now() - startTime,**

      **finishReason: 'stop',**

    **};**

  **}**



  **async chatStream(request: AIRequest, callback: AIStreamCallback): Promise<void> {**

    **const stream = await this.client.chat({**

      **model: request.model.id,**

      **messages: request.messages.map((m) => ({**

        **role: m.role as 'system' | 'user' | 'assistant',**

        **content: m.content,**

      **})),**

      **stream: true,**

      **options: {**

        **temperature: request.temperature ?? 0.7,**

        **num\_predict: request.maxTokens ?? 4096,**

      **},**

    **});**



    **for await (const chunk of stream) {**

      **callback({**

        **content: chunk.message.content,**

        **done: chunk.done,**

      **});**

    **}**

  **}**



  **async listModels(): Promise<ModelConfig\[]> {**

    **try {**

      **const response = await this.client.list();**

      **return response.models.map((model) => ({**

        **id: model.name,**

        **name: model.name,**

        **provider: 'ollama' as const,**

        **maxTokens: 4096,**

        **contextWindow: 8192,**

        **isLocal: true,**

        **size: model.size,**

        **parameterSize: model.details?.parameter\_size,**

        **quantization: model.details?.quantization\_level,**

      **}));**

    **} catch {**

      **return \[];**

    **}**

  **}**



  **async validateConnection(): Promise<boolean> {**

    **try {**

      **await this.client.list();**

      **return true;**

    **} catch {**

      **return false;**

    **}**

  **}**



  **async pullModel(modelName: string, onProgress?: (progress: number) => void): Promise<void> {**

    **const stream = await this.client.pull({ model: modelName, stream: true });**

    **for await (const chunk of stream) {**

      **if (onProgress \&\& chunk.total) {**

        **onProgress((chunk.completed || 0) / chunk.total);**

      **}**

    **}**

  **}**



  **async deleteModel(modelName: string): Promise<void> {**

    **await this.client.delete({ model: modelName });**

  **}**



  **async generateEmbeddings(model: string, text: string): Promise<number\[]> {**

    **const response = await this.client.embeddings({**

      **model,**

      **prompt: text,**

    **});**

    **return response.embedding;**

  **}**

**}**



### **8. Anthropic Provider (src/backend/ai/providers/anthropic.ts)**

**import Anthropic from '@anthropic-ai/sdk';**

**import { BaseProvider } from './base-provider';**

**import {**

  **AIRequest,**

  **AIResponse,**

  **AIStreamCallback,**

  **ModelConfig,**

**} from '../../../shared/types/ai.types';**



**export class AnthropicProvider extends BaseProvider {**

  **private client: Anthropic;**



  **constructor(apiKey?: string) {**

    **super({ apiKey: apiKey || process.env.ANTHROPIC\_API\_KEY || '' });**

    **this.client = new Anthropic({ apiKey: this.apiKey });**

  **}**



  **async chat(request: AIRequest): Promise<AIResponse> {**

    **const startTime = Date.now();**



    **const systemMessage = request.messages.find((m) => m.role === 'system');**

    **const messages = request.messages**

      **.filter((m) => m.role !== 'system')**

      **.map((m) => ({**

        **role: m.role as 'user' | 'assistant',**

        **content: m.content,**

      **}));**



    **const response = await this.client.messages.create({**

      **model: request.model.id,**

      **max\_tokens: request.maxTokens || 8192,**

      **temperature: request.temperature ?? 0.7,**

      **system: systemMessage?.content || '',**

      **messages,**

      **top\_p: request.topP,**

      **stop\_sequences: request.stop,**

    **});**



    **const textContent = response.content**

      **.filter((block): block is Anthropic.TextBlock => block.type === 'text')**

      **.map((block) => block.text)**

      **.join('');**



    **return {**

      **content: textContent,**

      **model: request.model.id,**

      **provider: 'anthropic',**

      **usage: {**

        **promptTokens: response.usage.input\_tokens,**

        **completionTokens: response.usage.output\_tokens,**

        **totalTokens: response.usage.input\_tokens + response.usage.output\_tokens,**

      **},**

      **latency: Date.now() - startTime,**

      **finishReason: response.stop\_reason || 'stop',**

    **};**

  **}**



  **async chatStream(request: AIRequest, callback: AIStreamCallback): Promise<void> {**

    **const systemMessage = request.messages.find((m) => m.role === 'system');**

    **const messages = request.messages**

      **.filter((m) => m.role !== 'system')**

      **.map((m) => ({**

        **role: m.role as 'user' | 'assistant',**

        **content: m.content,**

      **}));**



    **const stream = this.client.messages.stream({**

      **model: request.model.id,**

      **max\_tokens: request.maxTokens || 8192,**

      **temperature: request.temperature ?? 0.7,**

      **system: systemMessage?.content || '',**

      **messages,**

    **});**



    **for await (const event of stream) {**

      **if (**

        **event.type === 'content\_block\_delta' \&\&**

        **event.delta.type === 'text\_delta'**

      **) {**

        **callback({**

          **content: event.delta.text,**

          **done: false,**

        **});**

      **}**

    **}**



    **callback({ content: '', done: true });**

  **}**



  **async listModels(): Promise<ModelConfig\[]> {**

    **return \[**

      **{**

        **id: 'claude-sonnet-4-20250514',**

        **name: 'Claude 3.5 Sonnet',**

        **provider: 'anthropic',**

        **maxTokens: 8192,**

        **contextWindow: 200000,**

        **costPer1kInput: 0.003,**

        **costPer1kOutput: 0.015,**

      **},**

      **{**

        **id: 'claude-3-5-haiku-20241022',**

        **name: 'Claude 3.5 Haiku',**

        **provider: 'anthropic',**

        **maxTokens: 8192,**

        **contextWindow: 200000,**

        **costPer1kInput: 0.001,**

        **costPer1kOutput: 0.005,**

      **},**

      **{**

        **id: 'claude-3-opus-20240229',**

        **name: 'Claude 3 Opus',**

        **provider: 'anthropic',**

        **maxTokens: 4096,**

        **contextWindow: 200000,**

        **costPer1kInput: 0.015,**

        **costPer1kOutput: 0.075,**

      **},**

    **];**

  **}**



  **async validateConnection(): Promise<boolean> {**

    **try {**

      **await this.client.messages.create({**

        **model: 'claude-sonnet-4-20250514',**

        **max\_tokens: 10,**

        **messages: \[{ role: 'user', content: 'ping' }],**

      **});**

      **return true;**

    **} catch {**

      **return false;**

    **}**

  **}**

**}**



### **9. Multi-Agent System (src/backend/ai/agents/agent-manager.ts)**

**import { EventEmitter } from 'events';**

**import { v4 as uuid } from 'uuid';**

**import { AIEngine } from '../engine';**

**import { MemoryStore } from './memory-store';**

**import { TaskQueue } from './task-queue';**

**import {**

  **Agent,**

  **AgentConfig,**

  **AgentMessage,**

  **AgentTask,**

  **AgentStatus,**

  **AgentWorkflow,**

  **WorkflowResult,**

**} from '../../../shared/types/agent.types';**



**export class AgentManager extends EventEmitter {**

  **private agents: Map<string, Agent> = new Map();**

  **private aiEngine: AIEngine;**

  **private memoryStore: MemoryStore;**

  **private taskQueue: TaskQueue;**

  **private activeWorkflows: Map<string, AgentWorkflow> = new Map();**



  **constructor(aiEngine: AIEngine) {**

    **super();**

    **this.aiEngine = aiEngine;**

    **this.memoryStore = new MemoryStore();**

    **this.taskQueue = new TaskQueue();**

    **this.registerDefaultAgents();**

  **}**



  **private registerDefaultAgents() {**

    **// Architect Agent - System design and planning**

    **this.registerAgent({**

      **id: 'architect',**

      **name: 'Architect Agent',**

      **role: 'architect',**

      **description: 'Designs system architecture, plans project structure, and creates technical specifications',**

      **systemPrompt: `You are a senior software architect. Your responsibilities:**

        **1. Analyze requirements and propose system architecture**

        **2. Design database schemas and API contracts**

        **3. Plan project folder structure and module organization**

        **4. Identify potential scalability and performance concerns**

        **5. Create technical specifications and design documents**

        

        **Always provide structured, actionable output. Use diagrams (mermaid) when helpful.**

        **Consider trade-offs and explain your architectural decisions.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'search-tool', 'browser-tool'],**

      **temperature: 0.4,**

      **maxTokens: 8192,**

    **});**



    **// Coder Agent - Code generation**

    **this.registerAgent({**

      **id: 'coder',**

      **name: 'Coder Agent',**

      **role: 'coder',**

      **description: 'Generates high-quality, production-ready code',**

      **systemPrompt: `You are an expert software engineer. Your responsibilities:**

        **1. Write clean, efficient, well-documented code**

        **2. Follow best practices and design patterns**

        **3. Handle edge cases and error scenarios**

        **4. Write type-safe code with proper interfaces**

        **5. Include inline comments for complex logic**

        

        **Always produce complete, runnable code. Never use placeholder comments like "// TODO" or "// implement this".**

        **Follow the project's existing coding style and conventions.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'terminal-tool', 'search-tool'],**

      **temperature: 0.2,**

      **maxTokens: 8192,**

    **});**



    **// Reviewer Agent - Code review**

    **this.registerAgent({**

      **id: 'reviewer',**

      **name: 'Reviewer Agent',**

      **role: 'reviewer',**

      **description: 'Reviews code for quality, security, and best practices',**

      **systemPrompt: `You are a meticulous code reviewer. Your responsibilities:**

        **1. Check for bugs, logical errors, and edge cases**

        **2. Evaluate code quality, readability, and maintainability**

        **3. Identify security vulnerabilities (OWASP Top 10)**

        **4. Suggest performance optimizations**

        **5. Ensure consistent coding style and conventions**

        **6. Rate code quality on a scale of 1-10**

        

        **Provide specific, actionable feedback with code suggestions.**

        **Format issues as: \[SEVERITY] Line X: Description -> Suggestion`,**

      **model: { id: 'gpt-4o', provider: 'openai' },**

      **tools: \['file-tool', 'search-tool', 'linter-tool'],**

      **temperature: 0.1,**

      **maxTokens: 4096,**

    **});**



    **// Debugger Agent - Bug finding and fixing**

    **this.registerAgent({**

      **id: 'debugger',**

      **name: 'Debugger Agent',**

      **role: 'debugger',**

      **description: 'Identifies and fixes bugs in code',**

      **systemPrompt: `You are an expert debugger. Your responsibilities:**

        **1. Analyze error messages and stack traces**

        **2. Identify root causes of bugs**

        **3. Propose and implement fixes**

        **4. Add error handling and logging**

        **5. Write regression tests for fixed bugs**

        

        **Always explain the root cause before suggesting a fix.**

        **Consider potential side effects of your fixes.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'terminal-tool', 'search-tool', 'test-runner-tool'],**

      **temperature: 0.2,**

      **maxTokens: 4096,**

    **});**



    **// Tester Agent - Test generation**

    **this.registerAgent({**

      **id: 'tester',**

      **name: 'Tester Agent',**

      **role: 'tester',**

      **description: 'Generates comprehensive test suites',**

      **systemPrompt: `You are a QA engineer specializing in automated testing. Your responsibilities:**

        **1. Write unit tests with high coverage**

        **2. Create integration tests for API endpoints**

        **3. Design end-to-end test scenarios**

        **4. Generate edge case and boundary tests**

        **5. Create test fixtures and mock data**

        

        **Use the project's testing framework. Aim for >90% code coverage.**

        **Include both positive and negative test cases.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'terminal-tool', 'test-runner-tool'],**

      **temperature: 0.3,**

      **maxTokens: 8192,**

    **});**



    **// Security Agent - Security auditing**

    **this.registerAgent({**

      **id: 'security',**

      **name: 'Security Agent',**

      **role: 'security',**

      **description: 'Performs security analysis and vulnerability assessment',**

      **systemPrompt: `You are a cybersecurity expert. Your responsibilities:**

        **1. Identify security vulnerabilities (OWASP Top 10, CWE)**

        **2. Check for injection attacks, XSS, CSRF, etc.**

        **3. Review authentication and authorization logic**

        **4. Audit dependency security (known CVEs)**

        **5. Recommend security best practices and fixes**

        

        **Classify findings by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO.**

        **Provide CVE references when applicable.`,**

      **model: { id: 'gpt-4o', provider: 'openai' },**

      **tools: \['file-tool', 'search-tool', 'terminal-tool'],**

      **temperature: 0.1,**

      **maxTokens: 4096,**

    **});**



    **// DevOps Agent - CI/CD and infrastructure**

    **this.registerAgent({**

      **id: 'devops',**

      **name: 'DevOps Agent',**

      **role: 'devops',**

      **description: 'Manages CI/CD, Docker, and infrastructure',**

      **systemPrompt: `You are a DevOps engineer. Your responsibilities:**

        **1. Create and optimize Dockerfiles and docker-compose**

        **2. Set up CI/CD pipelines (GitHub Actions, GitLab CI)**

        **3. Configure deployment strategies**

        **4. Manage environment variables and secrets**

        **5. Optimize build processes and caching**

        

        **Always follow security best practices for infrastructure.**

        **Use multi-stage builds and minimize image sizes.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'terminal-tool', 'docker-tool'],**

      **temperature: 0.3,**

      **maxTokens: 4096,**

    **});**



    **// Documentation Agent**

    **this.registerAgent({**

      **id: 'docs',**

      **name: 'Documentation Agent',**

      **role: 'docs',**

      **description: 'Generates comprehensive documentation',**

      **systemPrompt: `You are a technical writer. Your responsibilities:**

        **1. Write clear README files**

        **2. Generate API documentation**

        **3. Create JSDoc/TSDoc comments**

        **4. Write user guides and tutorials**

        **5. Maintain changelog and migration guides**

        

        **Write for both beginners and experienced developers.**

        **Include code examples and usage patterns.`,**

      **model: { id: 'claude-sonnet-4-20250514', provider: 'anthropic' },**

      **tools: \['file-tool', 'search-tool'],**

      **temperature: 0.5,**

      **maxTokens: 8192,**

    **});**



    **// Terminal Agent - Command execution**

    **this.registerAgent({**

      **id: 'terminal',**

      **name: 'Terminal Agent',**

      **role: 'terminal',**

      **description: 'Executes and suggests terminal commands',**

      **systemPrompt: `You are a command-line expert. Your responsibilities:**

        **1. Suggest optimal terminal commands for tasks**

        **2. Explain command options and flags**

        **3. Chain commands for complex operations**

        **4. Handle different OS environments (Linux, macOS, Windows)**

        **5. Debug command failures and suggest alternatives**

        

        **Always explain what each command does before executing.**

        **NEVER suggest destructive commands without explicit confirmation (rm -rf, etc.)`,**

      **model: { id: 'claude-3-5-haiku-20241022', provider: 'anthropic' },**

      **tools: \['terminal-tool', 'file-tool'],**

      **temperature: 0.1,**

      **maxTokens: 2048,**

    **});**



    **// Research Agent**

    **this.registerAgent({**

      **id: 'research',**

      **name: 'Research Agent',**

      **role: 'research',**

      **description: 'Researches libraries, APIs, and solutions',**

      **systemPrompt: `You are a technical researcher. Your responsibilities:**

        **1. Find the best libraries and tools for specific tasks**

        **2. Compare alternatives with pros/cons**

        **3. Find code examples and documentation**

        **4. Research best practices and patterns**

        **5. Stay updated on latest technologies**

        

        **Always provide sources and references.**

        **Compare at least 3 alternatives when recommending tools.`,**

      **model: { id: 'gpt-4o', provider: 'openai' },**

      **tools: \['browser-tool', 'search-tool'],**

      **temperature: 0.5,**

      **maxTokens: 4096,**

    **});**

  **}**



  **registerAgent(config: AgentConfig): Agent {**

    **const agent: Agent = {**

      **...config,**

      **status: 'idle',**

      **createdAt: new Date(),**

      **taskHistory: \[],**

      **memory: \[],**

    **};**



    **this.agents.set(config.id, agent);**

    **this.emit('agent:registered', agent);**

    **return agent;**

  **}**



  **getAgent(id: string): Agent | undefined {**

    **return this.agents.get(id);**

  **}**



  **getAllAgents(): Agent\[] {**

    **return Array.from(this.agents.values());**

  **}**



  **async executeTask(agentId: string, task: AgentTask): Promise<string> {**

    **const agent = this.agents.get(agentId);**

    **if (!agent) throw new Error(`Agent ${agentId} not found`);**



    **agent.status = 'working';**

    **this.emit('agent:status', { agentId, status: 'working' });**



    **try {**

      **// Retrieve relevant memories**

      **const memories = await this.memoryStore.recall(agentId, task.description);**



      **// Build messages with context**

      **const messages = \[**

        **{ role: 'system' as const, content: agent.systemPrompt },**

        **...memories.map((m) => ({**

          **role: 'assistant' as const,**

          **content: `\[Previous context]: ${m.content}`,**

        **})),**

        **{**

          **role: 'user' as const,**

          **content: this.buildTaskPrompt(task),**

        **},**

      **];**



      **// Execute with AI engine**

      **const response = await this.aiEngine.chat({**

        **model: {**

          **id: agent.model.id,**

          **name: agent.model.id,**

          **provider: agent.model.provider,**

          **maxTokens: agent.maxTokens || 4096,**

          **contextWindow: 128000,**

        **},**

        **messages,**

        **temperature: agent.temperature || 0.3,**

        **maxTokens: agent.maxTokens || 4096,**

        **context: {**

          **type: 'agent-task',**

          **agentId,**

          **taskId: task.id,**

        **},**

      **});**



      **// Store in memory**

      **await this.memoryStore.store(agentId, {**

        **task: task.description,**

        **result: response.content,**

        **timestamp: new Date(),**

      **});**



      **// Update agent**

      **agent.status = 'idle';**

      **agent.taskHistory.push({**

        **...task,**

        **result: response.content,**

        **completedAt: new Date(),**

      **});**



      **this.emit('agent:task-complete', { agentId, task, result: response.content });**

      **return response.content;**



    **} catch (error) {**

      **agent.status = 'error';**

      **this.emit('agent:error', { agentId, error });**

      **throw error;**

    **}**

  **}**



  **async executeWorkflow(workflow: AgentWorkflow): Promise<WorkflowResult> {**

    **const workflowId = uuid();**

    **this.activeWorkflows.set(workflowId, workflow);**

    **this.emit('workflow:started', { workflowId, workflow });**



    **const results: Map<string, string> = new Map();**



    **try {**

      **switch (workflow.type) {**

        **case 'sequential':**

          **for (const step of workflow.steps) {**

            **const context = this.buildStepContext(step, results);**

            **const result = await this.executeTask(step.agentId, {**

              **id: uuid(),**

              **description: step.instruction,**

              **context,**

              **priority: step.priority || 'normal',**

            **});**

            **results.set(step.id, result);**

            **this.emit('workflow:step-complete', { workflowId, stepId: step.id, result });**

          **}**

          **break;**



        **case 'parallel':**

          **const parallelPromises = workflow.steps.map((step) =>**

            **this.executeTask(step.agentId, {**

              **id: uuid(),**

              **description: step.instruction,**

              **context: step.context,**

              **priority: step.priority || 'normal',**

            **}).then((result) => {**

              **results.set(step.id, result);**

              **return result;**

            **})**

          **);**

          **await Promise.all(parallelPromises);**

          **break;**



        **case 'hierarchical':**

          **// Manager agent delegates to worker agents**

          **const managerStep = workflow.steps\[0];**

          **const managerResult = await this.executeTask(managerStep.agentId, {**

            **id: uuid(),**

            **description: managerStep.instruction,**

            **context: {**

              **availableAgents: workflow.steps.slice(1).map((s) => ({**

                **id: s.agentId,**

                **description: this.getAgent(s.agentId)?.description,**

              **})),**

            **},**

            **priority: 'high',**

          **});**

          **results.set(managerStep.id, managerResult);**



          **// Parse manager's delegation plan and execute**

          **const delegationPlan = this.parseDelegationPlan(managerResult);**

          **for (const delegation of delegationPlan) {**

            **const result = await this.executeTask(delegation.agentId, {**

              **id: uuid(),**

              **description: delegation.task,**

              **priority: 'normal',**

            **});**

            **results.set(delegation.agentId, result);**

          **}**

          **break;**



        **case 'consensus':**

          **// Multiple agents tackle same problem, then vote**

          **const consensusResults = await Promise.all(**

            **workflow.steps.map((step) =>**

              **this.executeTask(step.agentId, {**

                **id: uuid(),**

                **description: step.instruction,**

                **priority: 'normal',**

              **})**

            **)**

          **);**



          **// Use reviewer agent to synthesize consensus**

          **const synthesized = await this.executeTask('reviewer', {**

            **id: uuid(),**

            **description: `Synthesize these solutions and pick the best approach:\\n\\n${consensusResults.map((r, i) => `Solution ${i + 1}:\\n${r}`).join('\\n\\n---\\n\\n')}`,**

            **priority: 'high',**

          **});**

          **results.set('consensus', synthesized);**

          **break;**

      **}**



      **this.activeWorkflows.delete(workflowId);**

      **this.emit('workflow:completed', { workflowId, results });**



      **return {**

        **workflowId,**

        **results: Object.fromEntries(results),**

        **status: 'completed',**

      **};**



    **} catch (error) {**

      **this.activeWorkflows.delete(workflowId);**

      **this.emit('workflow:failed', { workflowId, error });**

      **throw error;**

    **}**

  **}**



  **// Inter-agent communication**

  **async sendMessage(from: string, to: string, message: AgentMessage): Promise<string> {**

    **this.emit('agent:message', { from, to, message });**



    **const targetAgent = this.agents.get(to);**

    **if (!targetAgent) throw new Error(`Agent ${to} not found`);**



    **return this.executeTask(to, {**

      **id: uuid(),**

      **description: `Message from ${from} agent: ${message.content}`,**

      **context: message.context,**

      **priority: message.priority || 'normal',**

    **});**

  **}**



  **private buildTaskPrompt(task: AgentTask): string {**

    **let prompt = task.description;**



    **if (task.context) {**

      **prompt += `\\n\\nContext:\\n${JSON.stringify(task.context, null, 2)}`;**

    **}**



    **if (task.files) {**

      **prompt += `\\n\\nRelevant files:\\n`;**

      **for (const file of task.files) {**

        **prompt += `\\n--- ${file.path} ---\\n${file.content}\\n`;**

      **}**

    **}**



    **return prompt;**

  **}**



  **private buildStepContext(**

    **step: any,**

    **previousResults: Map<string, string>**

  **): any {**

    **const context: any = { ...step.context };**



    **if (step.dependsOn) {**

      **context.previousResults = {};**

      **for (const depId of step.dependsOn) {**

        **context.previousResults\[depId] = previousResults.get(depId);**

      **}**

    **}**



    **return context;**

  **}**



  **private parseDelegationPlan(**

    **managerOutput: string**

  **): Array<{ agentId: string; task: string }> {**

    **// Parse JSON delegation plan from manager output**

    **try {**

      **const jsonMatch = managerOutput.match(/```json\\n(\[\\s\\S]\*?)```/);**

      **if (jsonMatch) {**

        **return JSON.parse(jsonMatch\[1]);**

      **}**

    **} catch {}**



    **return \[];**

  **}**

**}**



### **10. Terminal PTY Manager (src/backend/terminal/pty-manager.ts)**



**import \* as pty from 'node-pty';**

**import os from 'os';**

**import { v4 as uuid } from 'uuid';**

**import { EventEmitter } from 'events';**



**interface TerminalOptions {**

  **shell?: string;**

  **cwd?: string;**

  **env?: Record<string, string>;**

  **cols?: number;**

  **rows?: number;**

**}**



**interface TerminalInstance {**

  **id: string;**

  **process: pty.IPty;**

  **shell: string;**

  **cwd: string;**

  **createdAt: Date;**

**}**



**export class PtyManager extends EventEmitter {**

  **private terminals: Map<string, TerminalInstance> = new Map();**

  **private dataCallbacks: Map<string, (data: string) => void> = new Map();**

  **private exitCallbacks: Map<string, (exitCode: number) => void> = new Map();**



  **getDefaultShell(): string {**

    **if (process.platform === 'win32') {**

      **return process.env.COMSPEC || 'powershell.exe';**

    **}**

    **return process.env.SHELL || '/bin/bash';**

  **}**



  **getAvailableShells(): Array<{ name: string; path: string }> {**

    **const shells = \[];**



    **if (process.platform === 'win32') {**

      **shells.push(**

        **{ name: 'PowerShell', path: 'powershell.exe' },**

        **{ name: 'PowerShell 7', path: 'pwsh.exe' },**

        **{ name: 'Command Prompt', path: 'cmd.exe' },**

        **{ name: 'Git Bash', path: 'C:\\\\Program Files\\\\Git\\\\bin\\\\bash.exe' },**

        **{ name: 'WSL', path: 'wsl.exe' }**

      **);**

    **} else if (process.platform === 'darwin') {**

      **shells.push(**

        **{ name: 'Zsh', path: '/bin/zsh' },**

        **{ name: 'Bash', path: '/bin/bash' },**

        **{ name: 'Fish', path: '/usr/local/bin/fish' },**

        **{ name: 'Nushell', path: '/usr/local/bin/nu' }**

      **);**

    **} else {**

      **shells.push(**

        **{ name: 'Bash', path: '/bin/bash' },**

        **{ name: 'Zsh', path: '/usr/bin/zsh' },**

        **{ name: 'Fish', path: '/usr/bin/fish' },**

        **{ name: 'Sh', path: '/bin/sh' }**

      **);**

    **}**



    **return shells;**

  **}**



  **createTerminal(options: TerminalOptions = {}): string {**

    **const id = uuid();**

    **const shell = options.shell || this.getDefaultShell();**

    **const cwd = options.cwd || os.homedir();**



    **const env = {**

      **...process.env,**

      **...options.env,**

      **TERM: 'xterm-256color',**

      **COLORTERM: 'truecolor',**

      **TERM\_PROGRAM: 'NexusIDE',**

      **NEXUS\_TERMINAL: '1',**

    **};**



    **const shellArgs = this.getShellArgs(shell);**



    **const ptyProcess = pty.spawn(shell, shellArgs, {**

      **name: 'xterm-256color',**

      **cols: options.cols || 120,**

      **rows: options.rows || 30,**

      **cwd,**

      **env: env as Record<string, string>,**

      **useConpty: process.platform === 'win32',**

    **});**



    **const instance: TerminalInstance = {**

      **id,**

      **process: ptyProcess,**

      **shell,**

      **cwd,**

      **createdAt: new Date(),**

    **};**



    **this.terminals.set(id, instance);**



    **// Handle data**

    **ptyProcess.onData((data) => {**

      **const callback = this.dataCallbacks.get(id);**

      **if (callback) callback(data);**

      **this.emit('data', { id, data });**

    **});**



    **// Handle exit**

    **ptyProcess.onExit(({ exitCode }) => {**

      **const callback = this.exitCallbacks.get(id);**

      **if (callback) callback(exitCode);**

      **this.emit('exit', { id, exitCode });**

      **this.terminals.delete(id);**

      **this.dataCallbacks.delete(id);**

      **this.exitCallbacks.delete(id);**

    **});**



    **this.emit('created', { id, shell, cwd });**

    **return id;**

  **}**



  **private getShellArgs(shell: string): string\[] {**

    **const shellName = shell.toLowerCase();**



    **if (shellName.includes('bash')) {**

      **return \['--login'];**

    **} else if (shellName.includes('zsh')) {**

      **return \['--login'];**

    **} else if (shellName.includes('fish')) {**

      **return \['--login'];**

    **} else if (shellName.includes('powershell') || shellName.includes('pwsh')) {**

      **return \['-NoLogo'];**

    **}**



    **return \[];**

  **}**



  **write(id: string, data: string) {**

    **const instance = this.terminals.get(id);**

    **if (instance) {**

      **instance.process.write(data);**

    **}**

  **}**



  **resize(id: string, cols: number, rows: number) {**

    **const instance = this.terminals.get(id);**

    **if (instance) {**

      **instance.process.resize(cols, rows);**

    **}**

  **}**



  **kill(id: string) {**

    **const instance = this.terminals.get(id);**

    **if (instance) {**

      **instance.process.kill();**

      **this.terminals.delete(id);**

    **}**

  **}**



  **killAll() {**

    **for (const \[id] of this.terminals) {**

      **this.kill(id);**

    **}**

  **}**



  **onData(id: string, callback: (data: string) => void) {**

    **this.dataCallbacks.set(id, callback);**

  **}**



  **onExit(id: string, callback: (exitCode: number) => void) {**

    **this.exitCallbacks.set(id, callback);**

  **}**



  **getTerminal(id: string): TerminalInstance | undefined {**

    **return this.terminals.get(id);**

  **}**



  **getAllTerminals(): TerminalInstance\[] {**

    **return Array.from(this.terminals.values());**

  **}**



  **getCwd(id: string): string {**

    **const instance = this.terminals.get(id);**

    **return instance?.cwd || os.homedir();**

  **}**



  **async executeCommand(**

    **command: string,**

    **cwd?: string**

  **): Promise<{ stdout: string; exitCode: number }> {**

    **return new Promise((resolve, reject) => {**

      **const id = this.createTerminal({ cwd });**

      **let output = '';**



      **this.onData(id, (data) => {**

        **output += data;**

      **});**



      **this.onExit(id, (exitCode) => {**

        **resolve({ stdout: output, exitCode });**

      **});**



      **// Write command and exit**

      **this.write(id, command + '\\r');**



      **// Timeout**

      **setTimeout(() => {**

        **this.kill(id);**

        **reject(new Error('Command timed out'));**

      **}, 30000);**

    **});**

  **}**

**}**



### **11. Database Manager (src/backend/database/db-manager.ts)**

**import Database from 'better-sqlite3';**

**import { Pool as PgPool } from 'pg';**

**import mysql from 'mysql2/promise';**

**import { MongoClient, Db as MongoDB } from 'mongodb';**

**import Redis from 'ioredis';**

**import { v4 as uuid } from 'uuid';**

**import { EventEmitter } from 'events';**



**interface DBConnection {**

  **id: string;**

  **type: 'sqlite' | 'postgresql' | 'mysql' | 'mongodb' | 'redis';**

  **name: string;**

  **config: any;**

  **client: any;**

  **status: 'connected' | 'disconnected' | 'error';**

  **createdAt: Date;**

**}**



**interface QueryResult {**

  **rows: any\[];**

  **fields?: string\[];**

  **rowCount: number;**

  **executionTime: number;**

  **error?: string;**

**}**



**export class DatabaseManager extends EventEmitter {**

  **private connections: Map<string, DBConnection> = new Map();**



  **async connect(config: {**

    **type: 'sqlite' | 'postgresql' | 'mysql' | 'mongodb' | 'redis';**

    **name: string;**

    **host?: string;**

    **port?: number;**

    **database?: string;**

    **username?: string;**

    **password?: string;**

    **filepath?: string; // For SQLite**

    **connectionString?: string;**

  **}): Promise<string> {**

    **const id = uuid();**



    **try {**

      **let client: any;**



      **switch (config.type) {**

        **case 'sqlite':**

          **client = new Database(config.filepath || ':memory:', {**

            **verbose: console.log,**

          **});**

          **break;**



        **case 'postgresql':**

          **client = new PgPool({**

            **host: config.host || 'localhost',**

            **port: config.port || 5432,**

            **database: config.database,**

            **user: config.username,**

            **password: config.password,**

            **connectionString: config.connectionString,**

            **max: 10,**

          **});**

          **// Test connection**

          **await client.query('SELECT 1');**

          **break;**



        **case 'mysql':**

          **client = await mysql.createPool({**

            **host: config.host || 'localhost',**

            **port: config.port || 3306,**

            **database: config.database,**

            **user: config.username,**

            **password: config.password,**

            **waitForConnections: true,**

            **connectionLimit: 10,**

          **});**

          **// Test connection**

          **await client.query('SELECT 1');**

          **break;**



        **case 'mongodb':**

          **const mongoUrl = config.connectionString ||**

            **`mongodb://${config.username}:${config.password}@${config.host || 'localhost'}:${config.port || 27017}/${config.database}`;**

          **client = new MongoClient(mongoUrl);**

          **await client.connect();**

          **break;**



        **case 'redis':**

          **client = new Redis({**

            **host: config.host || 'localhost',**

            **port: config.port || 6379,**

            **password: config.password,**

            **db: 0,**

          **});**

          **await client.ping();**

          **break;**

      **}**



      **const connection: DBConnection = {**

        **id,**

        **type: config.type,**

        **name: config.name,**

        **config,**

        **client,**

        **status: 'connected',**

        **createdAt: new Date(),**

      **};**



      **this.connections.set(id, connection);**

      **this.emit('connected', { id, type: config.type, name: config.name });**



      **return id;**

    **} catch (error) {**

      **this.emit('error', { id, error });**

      **throw error;**

    **}**

  **}**



  **async disconnect(connectionId: string): Promise<void> {**

    **const conn = this.connections.get(connectionId);**

    **if (!conn) throw new Error('Connection not found');**



    **try {**

      **switch (conn.type) {**

        **case 'sqlite':**

          **conn.client.close();**

          **break;**

        **case 'postgresql':**

          **await conn.client.end();**

          **break;**

        **case 'mysql':**

          **await conn.client.end();**

          **break;**

        **case 'mongodb':**

          **await conn.client.close();**

          **break;**

        **case 'redis':**

          **conn.client.disconnect();**

          **break;**

      **}**



      **conn.status = 'disconnected';**

      **this.connections.delete(connectionId);**

      **this.emit('disconnected', { id: connectionId });**

    **} catch (error) {**

      **conn.status = 'error';**

      **throw error;**

    **}**

  **}**



  **async executeQuery(connectionId: string, query: string): Promise<QueryResult> {**

    **const conn = this.connections.get(connectionId);**

    **if (!conn) throw new Error('Connection not found');**



    **const startTime = Date.now();**



    **try {**

      **let result: QueryResult;**



      **switch (conn.type) {**

        **case 'sqlite': {**

          **const isSelect = query.trim().toUpperCase().startsWith('SELECT') ||**

                          **query.trim().toUpperCase().startsWith('PRAGMA');**



          **if (isSelect) {**

            **const rows = conn.client.prepare(query).all();**

            **const fields = rows.length > 0 ? Object.keys(rows\[0]) : \[];**

            **result = {**

              **rows,**

              **fields,**

              **rowCount: rows.length,**

              **executionTime: Date.now() - startTime,**

            **};**

          **} else {**

            **const info = conn.client.prepare(query).run();**

            **result = {**

              **rows: \[],**

              **rowCount: info.changes,**

              **executionTime: Date.now() - startTime,**

            **};**

          **}**

          **break;**

        **}**



        **case 'postgresql': {**

          **const pgResult = await conn.client.query(query);**

          **result = {**

            **rows: pgResult.rows,**

            **fields: pgResult.fields?.map((f: any) => f.name),**

            **rowCount: pgResult.rowCount || pgResult.rows.length,**

            **executionTime: Date.now() - startTime,**

          **};**

          **break;**

        **}**



        **case 'mysql': {**

          **const \[rows, fields] = await conn.client.execute(query);**

          **result = {**

            **rows: Array.isArray(rows) ? rows : \[],**

            **fields: Array.isArray(fields)**

              **? fields.map((f: any) => f.name)**

              **: undefined,**

            **rowCount: Array.isArray(rows) ? rows.length : 0,**

            **executionTime: Date.now() - startTime,**

          **};**

          **break;**

        **}**



        **case 'mongodb': {**

          **// Parse MongoDB command from pseudo-SQL or native format**

          **const db: MongoDB = conn.client.db(conn.config.database);**

          **const parsed = this.parseMongoQuery(query);**

          **const collection = db.collection(parsed.collection);**



          **let mongoResult: any;**

          **switch (parsed.operation) {**

            **case 'find':**

              **mongoResult = await collection.find(parsed.filter).limit(1000).toArray();**

              **break;**

            **case 'insert':**

              **mongoResult = await collection.insertMany(parsed.documents);**

              **break;**

            **case 'update':**

              **mongoResult = await collection.updateMany(parsed.filter, parsed.update);**

              **break;**

            **case 'delete':**

              **mongoResult = await collection.deleteMany(parsed.filter);**

              **break;**

            **case 'aggregate':**

              **mongoResult = await collection.aggregate(parsed.pipeline).toArray();**

              **break;**

            **default:**

              **mongoResult = \[];**

          **}**



          **const rows = Array.isArray(mongoResult) ? mongoResult : \[mongoResult];**

          **result = {**

            **rows,**

            **rowCount: rows.length,**

            **executionTime: Date.now() - startTime,**

          **};**

          **break;**

        **}**



        **case 'redis': {**

          **const args = query.split(' ');**

          **const command = args\[0].toUpperCase();**

          **const redisResult = await conn.client.call(command, ...args.slice(1));**

          **result = {**

            **rows: \[{ result: redisResult }],**

            **rowCount: 1,**

            **executionTime: Date.now() - startTime,**

          **};**

          **break;**

        **}**



        **default:**

          **throw new Error(`Unsupported database type: ${conn.type}`);**

      **}**



      **this.emit('query:executed', {**

        **connectionId,**

        **query,**

        **result,**

      **});**



      **return result;**

    **} catch (error) {**

      **const errorResult: QueryResult = {**

        **rows: \[],**

        **rowCount: 0,**

        **executionTime: Date.now() - startTime,**

        **error: error instanceof Error ? error.message : String(error),**

      **};**



      **this.emit('query:error', { connectionId, query, error });**

      **return errorResult;**

    **}**

  **}**



  **async getTables(connectionId: string): Promise<string\[]> {**

    **const conn = this.connections.get(connectionId);**

    **if (!conn) throw new Error('Connection not found');**



    **switch (conn.type) {**

      **case 'sqlite': {**

        **const rows = conn.client**

          **.prepare("SELECT name FROM sqlite\_master WHERE type='table' ORDER BY name")**

          **.all();**

        **return rows.map((r: any) => r.name);**

      **}**

      **case 'postgresql': {**

        **const result = await conn.client.query(**

          **"SELECT tablename FROM pg\_tables WHERE schemaname = 'public' ORDER BY tablename"**

        **);**

        **return result.rows.map((r: any) => r.tablename);**

      **}**

      **case 'mysql': {**

        **const \[rows] = await conn.client.execute('SHOW TABLES');**

        **return (rows as any\[]).map((r) => Object.values(r)\[0] as string);**

      **}**

      **case 'mongodb': {**

        **const db: MongoDB = conn.client.db(conn.config.database);**

        **const collections = await db.listCollections().toArray();**

        **return collections.map((c) => c.name);**

      **}**

      **default:**

        **return \[];**

    **}**

  **}**



  **async getTableSchema(**

    **connectionId: string,**

    **tableName: string**

  **): Promise<Array<{**

    **name: string;**

    **type: string;**

    **nullable: boolean;**

    **primaryKey: boolean;**

    **defaultValue: any;**

  **}>> {**

    **const conn = this.connections.get(connectionId);**

    **if (!conn) throw new Error('Connection not found');**



    **switch (conn.type) {**

      **case 'sqlite': {**

        **const rows = conn.client.prepare(`PRAGMA table\_info("${tableName}")`).all();**

        **return rows.map((r: any) => ({**

          **name: r.name,**

          **type: r.type,**

          **nullable: !r.notnull,**

          **primaryKey: !!r.pk,**

          **defaultValue: r.dflt\_value,**

        **}));**

      **}**

      **case 'postgresql': {**

        **const result = await conn.client.query(`**

          **SELECT column\_name, data\_type, is\_nullable, column\_default,**

            **(SELECT COUNT(\*) FROM information\_schema.key\_column\_usage k**

             **WHERE k.table\_name = c.table\_name AND k.column\_name = c.column\_name) > 0 as is\_pk**

          **FROM information\_schema.columns c**

          **WHERE table\_name = $1 AND table\_schema = 'public'**

          **ORDER BY ordinal\_position**

        **`, \[tableName]);**

        **return result.rows.map((r: any) => ({**

          **name: r.column\_name,**

          **type: r.data\_type,**

          **nullable: r.is\_nullable === 'YES',**

          **primaryKey: r.is\_pk,**

          **defaultValue: r.column\_default,**

        **}));**

      **}**

      **case 'mysql': {**

        **const \[rows] = await conn.client.execute(`DESCRIBE \\`${tableName}\\``);**

        **return (rows as any\[]).map((r) => ({**

          **name: r.Field,**

          **type: r.Type,**

          **nullable: r.Null === 'YES',**

          **primaryKey: r.Key === 'PRI',**

          **defaultValue: r.Default,**

        **}));**

      **}**

      **default:**

        **return \[];**

    **}**

  **}**



  **getConnections(): Array<{**

    **id: string;**

    **type: string;**

    **name: string;**

    **status: string;**

  **}> {**

    **return Array.from(this.connections.values()).map((c) => ({**

      **id: c.id,**

      **type: c.type,**

      **name: c.name,**

      **status: c.status,**

    **}));**

  **}**



  **private parseMongoQuery(query: string): any {**

    **try {**

      **return JSON.parse(query);**

    **} catch {**

      **// Basic parsing for simple queries**

      **return {**

        **collection: 'default',**

        **operation: 'find',**

        **filter: {},**

      **};**

    **}**

  **}**

**}**

### **12. Main React App (src/renderer/App.tsx)**

**import React, { useEffect, useState } from 'react';**

**import { MainLayout } from './components/Layout/MainLayout';**

**import { CommandCenter } from './components/Layout/CommandCenter';**

**import { useSettingsStore } from './store/settingsStore';**

**import { useFileStore } from './store/fileStore';**

**import { Toaster } from 'sonner';**

**import './styles/global.css';**



**export default function App() {**

  **const { theme, loadSettings } = useSettingsStore();**

  **const { setWorkspacePath } = useFileStore();**

  **const \[isReady, setIsReady] = useState(false);**



  **useEffect(() => {**

    **const init = async () => {**

      **// Load user settings**

      **await loadSettings();**



      **// Listen for folder open**

      **window.electronAPI.onOpenFolder((path: string) => {**

        **setWorkspacePath(path);**

      **});**



      **// Listen for file open**

      **window.electronAPI.onOpenFile((path: string) => {**

        **// Handle opening file**

      **});**



      **setIsReady(true);**

    **};**



    **init();**

  **}, \[]);**



  **if (!isReady) {**

    **return (**

      **<div className="flex items-center justify-center h-screen bg-\[#0d1117]">**

        **<div className="text-center">**

          **<div className="animate-pulse">**

            **<h1 className="text-4xl font-bold text-white mb-2">⚡ Nexus IDE</h1>**

            **<p className="text-gray-400">Initializing AI-Powered Development Environment...</p>**

          **</div>**

          **<div className="mt-8 w-64 h-1 bg-gray-800 rounded-full overflow-hidden mx-auto">**

            **<div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-loading-bar" />**

          **</div>**

        **</div>**

      **</div>**

    **);**

  **}**



  **return (**

    **<div className={`h-screen ${theme}`} data-theme={theme}>**

      **<MainLayout />**

      **<CommandCenter />**

      **<Toaster**

        **position="bottom-right"**

        **theme={theme === 'dark' ? 'dark' : 'light'}**

        **richColors**

      **/>**

    **</div>**

  **);**

**}**



### **13. Main Layout (src/renderer/components/Layout/MainLayout.tsx)**



**import React, { useState } from 'react';**

**import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';**

**import { ActivityBar } from './ActivityBar';**

**import { Sidebar } from './Sidebar';**

**import { StatusBar } from './StatusBar';**

**import { MonacoEditor } from '../Editor/MonacoEditor';**

**import { EditorTabs } from '../Editor/EditorTabs';**

**import { TerminalPanel } from '../Terminal/TerminalPanel';**

**import { ChatInterface } from '../AIPanel/ChatInterface';**

**import { FileTree } from '../FileExplorer/FileTree';**

**import { GitPanel } from '../Git/GitPanel';**

**import { DatabaseExplorer } from '../Database/DatabaseExplorer';**

**import { ExtensionMarketplace } from '../Extensions/ExtensionMarketplace';**

**import { SearchFiles } from '../FileExplorer/SearchFiles';**

**import { useEditorStore } from '../../store/editorStore';**



**type SidebarView = 'files' | 'search' | 'git' | 'database' | 'extensions' | 'ai';**



**export function MainLayout() {**

  **const \[activeSidebarView, setActiveSidebarView] = useState<SidebarView>('files');**

  **const \[showSidebar, setShowSidebar] = useState(true);**

  **const \[showPanel, setShowPanel] = useState(true);**

  **const \[showAIPanel, setShowAIPanel] = useState(true);**

  **const \[panelView, setPanelView] = useState<'terminal' | 'problems' | 'output'>('terminal');**

  **const { openFiles, activeFileId } = useEditorStore();**



  **const sidebarContent = {**

    **files: <FileTree />,**

    **search: <SearchFiles />,**

    **git: <GitPanel />,**

    **database: <DatabaseExplorer />,**

    **extensions: <ExtensionMarketplace />,**

    **ai: <ChatInterface />,**

  **};**



  **return (**

    **<div className="h-screen flex flex-col bg-\[#0d1117] text-gray-200">**

      **{/\* Title Bar (for custom title bar on macOS) \*/}**

      **<div className="h-8 bg-\[#010409] flex items-center justify-center drag-region border-b border-\[#21262d]">**

        **<span className="text-xs text-gray-500 font-medium">**

          **⚡ Nexus IDE**

          **{activeFileId \&\& ` — ${activeFileId}`}**

        **</span>**

      **</div>**



      **{/\* Main Content \*/}**

      **<div className="flex-1 flex overflow-hidden">**

        **{/\* Activity Bar \*/}**

        **<ActivityBar**

          **activeView={activeSidebarView}**

          **onViewChange={(view) => {**

            **if (view === activeSidebarView \&\& showSidebar) {**

              **setShowSidebar(false);**

            **} else {**

              **setActiveSidebarView(view);**

              **setShowSidebar(true);**

            **}**

          **}}**

          **onToggleAI={() => setShowAIPanel(!showAIPanel)}**

          **showAI={showAIPanel}**

        **/>**



        **{/\* Main Panel Group \*/}**

        **<PanelGroup direction="horizontal" className="flex-1">**

          **{/\* Sidebar \*/}**

          **{showSidebar \&\& (**

            **<>**

              **<Panel**

                **defaultSize={20}**

                **minSize={15}**

                **maxSize={40}**

                **className="bg-\[#0d1117] border-r border-\[#21262d]"**

              **>**

                **<div className="h-full flex flex-col">**

                  **<div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-\[#21262d]">**

                    **{activeSidebarView}**

                  **</div>**

                  **<div className="flex-1 overflow-auto">**

                    **{sidebarContent\[activeSidebarView]}**

                  **</div>**

                **</div>**

              **</Panel>**

              **<PanelResizeHandle className="w-1 bg-\[#21262d] hover:bg-blue-500 transition-colors cursor-col-resize" />**

            **</>**

          **)}**



          **{/\* Editor Area \*/}**

          **<Panel defaultSize={showAIPanel ? 50 : 80} minSize={30}>**

            **<PanelGroup direction="vertical">**

              **{/\* Editor \*/}**

              **<Panel defaultSize={showPanel ? 65 : 100} minSize={30}>**

                **<div className="h-full flex flex-col">**

                  **<EditorTabs />**

                  **<div className="flex-1">**

                    **{openFiles.length > 0 ? (**

                      **<MonacoEditor />**

                    **) : (**

                      **<WelcomeScreen />**

                    **)}**

                  **</div>**

                **</div>**

              **</Panel>**



              **{/\* Bottom Panel (Terminal/Problems/Output) \*/}**

              **{showPanel \&\& (**

                **<>**

                  **<PanelResizeHandle className="h-1 bg-\[#21262d] hover:bg-blue-500 transition-colors cursor-row-resize" />**

                  **<Panel defaultSize={35} minSize={15} maxSize={70}>**

                    **<div className="h-full flex flex-col bg-\[#0d1117]">**

                      **{/\* Panel Tabs \*/}**

                      **<div className="flex items-center border-b border-\[#21262d] px-2">**

                        **{(\['terminal', 'problems', 'output'] as const).map((view) => (**

                          **<button**

                            **key={view}**

                            **onClick={() => setPanelView(view)}**

                            **className={`px-3 py-1.5 text-xs font-medium capitalize transition-colors ${**

                              **panelView === view**

                                **? 'text-white border-b-2 border-blue-500'**

                                **: 'text-gray-400 hover:text-gray-200'**

                            **}`}**

                          **>**

                            **{view}**

                          **</button>**

                        **))}**

                        **<div className="flex-1" />**

                        **<button**

                          **onClick={() => setShowPanel(false)}**

                          **className="p-1 text-gray-400 hover:text-white"**

                        **>**

                          **✕**

                        **</button>**

                      **</div>**



                      **{/\* Panel Content \*/}**

                      **<div className="flex-1 overflow-hidden">**

                        **{panelView === 'terminal' \&\& <TerminalPanel />}**

                        **{panelView === 'problems' \&\& <ProblemsPanel />}**

                        **{panelView === 'output' \&\& <OutputPanel />}**

                      **</div>**

                    **</div>**

                  **</Panel>**

                **</>**

              **)}**

            **</PanelGroup>**

          **</Panel>**



          **{/\* AI Panel \*/}**

          **{showAIPanel \&\& (**

            **<>**

              **<PanelResizeHandle className="w-1 bg-\[#21262d] hover:bg-purple-500 transition-colors cursor-col-resize" />**

              **<Panel defaultSize={30} minSize={20} maxSize={50}>**

                **<ChatInterface />**

              **</Panel>**

            **</>**

          **)}**

        **</PanelGroup>**

      **</div>**



      **{/\* Status Bar \*/}**

      **<StatusBar**

        **onToggleTerminal={() => setShowPanel(!showPanel)}**

        **onToggleAI={() => setShowAIPanel(!showAIPanel)}**

      **/>**

    **</div>**

  **);**

**}**



**function WelcomeScreen() {**

  **return (**

    **<div className="h-full flex items-center justify-center bg-\[#0d1117]">**

      **<div className="text-center max-w-lg">**

        **<h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">**

          **⚡ Nexus IDE**

        **</h1>**

        **<p className="text-gray-400 mb-8">**

          **AI-Powered Development Environment with Multi-Agent Orchestration**

        **</p>**

        **<div className="grid grid-cols-2 gap-4 text-left">**

          **<ShortcutCard icon="📁" label="Open Folder" shortcut="Ctrl+O" />**

          **<ShortcutCard icon="📄" label="New File" shortcut="Ctrl+N" />**

          **<ShortcutCard icon="🤖" label="AI Chat" shortcut="Ctrl+L" />**

          **<ShortcutCard icon="💻" label="Terminal" shortcut="Ctrl+`" />**

          **<ShortcutCard icon="🔍" label="Search" shortcut="Ctrl+Shift+F" />**

          **<ShortcutCard icon="⌨️" label="Commands" shortcut="Ctrl+Shift+P" />**

        **</div>**

      **</div>**

    **</div>**

  **);**

**}**



**function ShortcutCard({ icon, label, shortcut }: { icon: string; label: string; shortcut: string }) {**

  **return (**

    **<div className="flex items-center gap-3 p-3 rounded-lg bg-\[#161b22] hover:bg-\[#1c2128] cursor-pointer transition-colors border border-\[#21262d]">**

      **<span className="text-xl">{icon}</span>**

      **<div>**

        **<div className="text-sm text-gray-200">{label}</div>**

        **<div className="text-xs text-gray-500">{shortcut}</div>**

      **</div>**

    **</div>**

  **);**

**}**



**function ProblemsPanel() {**

  **return <div className="p-4 text-gray-400 text-sm">No problems detected</div>;**

**}**



**function OutputPanel() {**

  **return <div className="p-4 text-gray-400 text-sm font-mono">Ready.</div>;**

**}**



**14. Terminal Component (src/renderer/components/Terminal/TerminalPanel.tsx)**



**import React, { useEffect, useRef, useState } from 'react';**

**import { Terminal } from '@xterm/xterm';**

**import { FitAddon } from '@xterm/addon-fit';**

**import { WebglAddon } from '@xterm/addon-webgl';**

**import { SearchAddon } from '@xterm/addon-search';**

**import { WebLinksAddon } from '@xterm/addon-web-links';**

**import '@xterm/xterm/css/xterm.css';**

**import { Plus, X, ChevronDown } from 'lucide-react';**



**interface TerminalInstance {**

  **id: string;**

  **terminal: Terminal;**

  **fitAddon: FitAddon;**

  **title: string;**

**}**



**export function TerminalPanel() {**

  **const \[terminals, setTerminals] = useState<TerminalInstance\[]>(\[]);**

  **const \[activeTerminalId, setActiveTerminalId] = useState<string | null>(null);**

  **const containerRef = useRef<HTMLDivElement>(null);**

  **const terminalRefs = useRef<Map<string, HTMLDivElement>>(new Map());**



  **const createTerminal = async () => {**

    **const shells = await window.electronAPI.invoke('terminal:getShells');**

    **const terminalId = await window.electronAPI.invoke('terminal:create', {**

      **shell: shells\[0]?.path,**

      **cwd: window.electronAPI.getWorkspacePath?.() || undefined,**

    **});**



    **const term = new Terminal({**

      **theme: {**

        **background: '#0d1117',**

        **foreground: '#c9d1d9',**

        **cursor: '#58a6ff',**

        **cursorAccent: '#0d1117',**

        **selectionBackground: '#264f78',**

        **selectionForeground: '#ffffff',**

        **black: '#484f58',**

        **red: '#ff7b72',**

        **green: '#3fb950',**

        **yellow: '#d29922',**

        **blue: '#58a6ff',**

        **magenta: '#bc8cff',**

        **cyan: '#39d2c0',**

        **white: '#b1bac4',**

        **brightBlack: '#6e7681',**

        **brightRed: '#ffa198',**

        **brightGreen: '#56d364',**

        **brightYellow: '#e3b341',**

        **brightBlue: '#79c0ff',**

        **brightMagenta: '#d2a8ff',**

        **brightCyan: '#56d4dd',**

        **brightWhite: '#f0f6fc',**

      **},**

      **fontSize: 14,**

      **fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, monospace',**

      **fontWeight: '400',**

      **lineHeight: 1.4,**

      **cursorBlink: true,**

      **cursorStyle: 'bar',**

      **scrollback: 10000,**

      **allowTransparency: true,**

      **macOptionIsMeta: true,**

      **macOptionClickForcesSelection: true,**

    **});**



    **const fitAddon = new FitAddon();**

    **const searchAddon = new SearchAddon();**

    **const webLinksAddon = new WebLinksAddon();**



    **term.loadAddon(fitAddon);**

    **term.loadAddon(searchAddon);**

    **term.loadAddon(webLinksAddon);**



    **const instance: TerminalInstance = {**

      **id: terminalId,**

      **terminal: term,**

      **fitAddon,**

      **title: `Terminal ${terminals.length + 1}`,**

    **};**



    **setTerminals((prev) => \[...prev, instance]);**

    **setActiveTerminalId(terminalId);**



    **// Wait for DOM to be ready**

    **setTimeout(() => {**

      **const container = terminalRefs.current.get(terminalId);**

      **if (container) {**

        **term.open(container);**



        **// Try WebGL addon for performance**

        **try {**

          **term.loadAddon(new WebglAddon());**

        **} catch {**

          **// Fall back to canvas renderer**

        **}**



        **fitAddon.fit();**

      **}**

    **}, 0);**



    **// Handle data from PTY**

    **window.electronAPI.on(`terminal:data:${terminalId}`, (\_: any, data: string) => {**

      **term.write(data);**

    **});**



    **// Handle user input**

    **term.onData((data) => {**

      **window.electronAPI.invoke('terminal:write', terminalId, data);**

    **});**



    **// Handle resize**

    **term.onResize(({ cols, rows }) => {**

      **window.electronAPI.invoke('terminal:resize', terminalId, cols, rows);**

    **});**



    **// Handle terminal exit**

    **window.electronAPI.on(`terminal:exit:${terminalId}`, () => {**

      **closeTerminal(terminalId);**

    **});**

  **};**



  **const closeTerminal = (id: string) => {**

    **const instance = terminals.find((t) => t.id === id);**

    **if (instance) {**

      **instance.terminal.dispose();**

      **window.electronAPI.invoke('terminal:kill', id);**

    **}**



    **setTerminals((prev) => prev.filter((t) => t.id !== id));**



    **if (activeTerminalId === id) {**

      **const remaining = terminals.filter((t) => t.id !== id);**

      **setActiveTerminalId(remaining.length > 0 ? remaining\[remaining.length - 1].id : null);**

    **}**

  **};**



  **// Create first terminal on mount**

  **useEffect(() => {**

    **if (terminals.length === 0) {**

      **createTerminal();**

    **}**

  **}, \[]);**



  **// Handle resize**

  **useEffect(() => {**

    **const handleResize = () => {**

      **const activeInstance = terminals.find((t) => t.id === activeTerminalId);**

      **if (activeInstance) {**

        **activeInstance.fitAddon.fit();**

      **}**

    **};**



    **const observer = new ResizeObserver(handleResize);**

    **if (containerRef.current) {**

      **observer.observe(containerRef.current);**

    **}**



    **return () => observer.disconnect();**

  **}, \[activeTerminalId, terminals]);**



  **return (**

    **<div className="h-full flex flex-col">**

      **{/\* Terminal Tabs \*/}**

      **<div className="flex items-center gap-1 px-2 py-1 border-b border-\[#21262d] bg-\[#010409]">**

        **{terminals.map((instance) => (**

          **<div**

            **key={instance.id}**

            **onClick={() => setActiveTerminalId(instance.id)}**

            **className={`flex items-center gap-2 px-3 py-1 rounded text-xs cursor-pointer transition-colors ${**

              **activeTerminalId === instance.id**

                **? 'bg-\[#161b22] text-white'**

                **: 'text-gray-400 hover:text-gray-200 hover:bg-\[#161b22]/50'**

            **}`}**

          **>**

            **<span className="text-green-400">⬤</span>**

            **<span>{instance.title}</span>**

            **<button**

              **onClick={(e) => {**

                **e.stopPropagation();**

                **closeTerminal(instance.id);**

              **}}**

              **className="hover:text-red-400 transition-colors"**

            **>**

              **<X size={12} />**

            **</button>**

          **</div>**

        **))}**



        **<button**

          **onClick={createTerminal}**

          **className="p-1 text-gray-400 hover:text-white rounded hover:bg-\[#161b22] transition-colors"**

        **>**

          **<Plus size={14} />**

        **</button>**

      **</div>**



      **{/\* Terminal Container \*/}**

      **<div ref={containerRef} className="flex-1 relative">**

        **{terminals.map((instance) => (**

          **<div**

            **key={instance.id}**

            **ref={(el) => {**

              **if (el) terminalRefs.current.set(instance.id, el);**

            **}}**

            **className="absolute inset-0 p-1"**

            **style={{**

              **display: activeTerminalId === instance.id ? 'block' : 'none',**

            **}}**

          **/>**

        **))}**

      **</div>**

    **</div>**

  **);**

**}**



**15. AI Chat Interface (src/renderer/components/AIPanel/ChatInterface.tsx)**



**import React, { useState, useRef, useEffect } from 'react';**

**import { Send, Paperclip, Settings, Bot, User, Copy, Check, RefreshCw, Sparkles } from 'lucide-react';**

**import { useAIStore } from '../../store/aiStore';**

**import { ModelSelector } from './ModelSelector';**

**import { StreamRenderer } from './StreamRenderer';**

**import { AgentOrchestrator } from './AgentOrchestrator';**

**import ReactMarkdown from 'react-markdown';**

**import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';**

**import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';**



**interface Message {**

  **id: string;**

  **role: 'user' | 'assistant' | 'system';**

  **content: string;**

  **timestamp: Date;**

  **model?: string;**

  **isStreaming?: boolean;**

  **codeBlocks?: Array<{ language: string; code: string; filePath?: string }>;**

**}**



**export function ChatInterface() {**

  **const \[input, setInput] = useState('');**

  **const \[messages, setMessages] = useState<Message\[]>(\[]);**

  **const \[isStreaming, setIsStreaming] = useState(false);**

  **const \[showModelSelector, setShowModelSelector] = useState(false);**

  **const \[showAgents, setShowAgents] = useState(false);**

  **const \[attachedFiles, setAttachedFiles] = useState<string\[]>(\[]);**

  **const messagesEndRef = useRef<HTMLDivElement>(null);**

  **const inputRef = useRef<HTMLTextAreaElement>(null);**

  **const { activeModel, sendMessage, streamMessage } = useAIStore();**



  **const scrollToBottom = () => {**

    **messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });**

  **};**



  **useEffect(() => {**

    **scrollToBottom();**

  **}, \[messages]);**



  **const handleSend = async () => {**

    **if (!input.trim() || isStreaming) return;**



    **const userMessage: Message = {**

      **id: crypto.randomUUID(),**

      **role: 'user',**

      **content: input,**

      **timestamp: new Date(),**

    **};**



    **setMessages((prev) => \[...prev, userMessage]);**

    **setInput('');**

    **setIsStreaming(true);**



    **const assistantMessage: Message = {**

      **id: crypto.randomUUID(),**

      **role: 'assistant',**

      **content: '',**

      **timestamp: new Date(),**

      **model: activeModel.name,**

      **isStreaming: true,**

    **};**



    **setMessages((prev) => \[...prev, assistantMessage]);**



    **try {**

      **// Get current editor context**

      **const editorContext = await getEditorContext();**



      **await streamMessage(**

        **{**

          **messages: \[**

            **...messages.map((m) => ({ role: m.role, content: m.content })),**

            **{ role: 'user', content: input },**

          **],**

          **context: editorContext,**

          **attachedFiles,**

        **},**

        **(chunk) => {**

          **setMessages((prev) =>**

            **prev.map((m) =>**

              **m.id === assistantMessage.id**

                **? { ...m, content: m.content + chunk.content }**

                **: m**

            **)**

          **);**

        **}**

      **);**

    **} catch (error) {**

      **setMessages((prev) =>**

        **prev.map((m) =>**

          **m.id === assistantMessage.id**

            **? { ...m, content: `Error: ${error}`, isStreaming: false }**

            **: m**

        **)**

      **);**

    **} finally {**

      **setIsStreaming(false);**

      **setMessages((prev) =>**

        **prev.map((m) =>**

          **m.id === assistantMessage.id**

            **? { ...m, isStreaming: false }**

            **: m**

        **)**

      **);**

      **setAttachedFiles(\[]);**

    **}**

  **};**



  **const handleKeyDown = (e: React.KeyboardEvent) => {**

    **if (e.key === 'Enter' \&\& !e.shiftKey) {**

      **e.preventDefault();**

      **handleSend();**

    **}**

  **};**



  **const applyCode = async (code: string, filePath?: string) => {**

    **if (filePath) {**

      **await window.electronAPI.invoke('fs:writeFile', filePath, code);**

    **}**

    **// Or apply to current editor**

  **};**



  **const getEditorContext = async () => {**

    **// Get context from current editor**

    **return {**

      **currentFile: null,**

      **selectedText: null,**

      **openFiles: \[],**

    **};**

  **};**



  **return (**

    **<div className="h-full flex flex-col bg-\[#0d1117]">**

      **{/\* Header \*/}**

      **<div className="flex items-center justify-between px-4 py-2 border-b border-\[#21262d]">**

        **<div className="flex items-center gap-2">**

          **<Sparkles size={16} className="text-purple-400" />**

          **<span className="text-sm font-semibold text-white">AI Assistant</span>**

        **</div>**

        **<div className="flex items-center gap-2">**

          **<button**

            **onClick={() => setShowAgents(!showAgents)}**

            **className="text-xs px-2 py-1 rounded bg-\[#161b22] text-gray-300 hover:text-white transition-colors border border-\[#21262d]"**

          **>**

            **🤖 Agents**

          **</button>**

          **<button**

            **onClick={() => setShowModelSelector(!showModelSelector)}**

            **className="text-xs px-2 py-1 rounded bg-\[#161b22] text-gray-300 hover:text-white transition-colors border border-\[#21262d]"**

          **>**

            **{activeModel.name}**

          **</button>**

        **</div>**

      **</div>**



      **{/\* Model Selector Dropdown \*/}**

      **{showModelSelector \&\& (**

        **<ModelSelector onClose={() => setShowModelSelector(false)} />**

      **)}**



      **{/\* Agent Orchestrator \*/}**

      **{showAgents \&\& (**

        **<AgentOrchestrator onClose={() => setShowAgents(false)} />**

      **)}**



      **{/\* Messages \*/}**

      **<div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">**

        **{messages.length === 0 \&\& (**

          **<div className="text-center py-12">**

            **<div className="text-4xl mb-4">🤖</div>**

            **<h3 className="text-lg font-semibold text-white mb-2">**

              **How can I help you code today?**

            **</h3>**

            **<p className="text-sm text-gray-400 mb-6">**

              **Ask me anything about your code, or use one of these suggestions:**

            **</p>**

            **<div className="grid grid-cols-1 gap-2 max-w-md mx-auto">**

              **{\[**

                **'💡 Explain the selected code',**

                **'🐛 Find and fix bugs in this file',**

                **'✨ Refactor for better performance',**

                **'🧪 Generate unit tests',**

                **'📝 Add documentation',**

                **'🔒 Security audit',**

              **].map((suggestion) => (**

                **<button**

                  **key={suggestion}**

                  **onClick={() => setInput(suggestion.substring(2))}**

                  **className="text-left px-4 py-2 rounded-lg bg-\[#161b22] text-sm text-gray-300 hover:text-white hover:bg-\[#1c2128] transition-colors border border-\[#21262d]"**

                **>**

                  **{suggestion}**

                **</button>**

              **))}**

            **</div>**

          **</div>**

        **)}**



        **{messages.map((message) => (**

          **<MessageBubble**

            **key={message.id}**

            **message={message}**

            **onApplyCode={applyCode}**

          **/>**

        **))}**



        **<div ref={messagesEndRef} />**

      **</div>**



      **{/\* Attached Files \*/}**

      **{attachedFiles.length > 0 \&\& (**

        **<div className="px-4 py-2 border-t border-\[#21262d] flex flex-wrap gap-2">**

          **{attachedFiles.map((file) => (**

            **<span**

              **key={file}**

              **className="inline-flex items-center gap-1 px-2 py-1 rounded bg-\[#161b22] text-xs text-gray-300 border border-\[#21262d]"**

            **>**

              **📎 {file.split('/').pop()}**

              **<button**

                **onClick={() =>**

                  **setAttachedFiles((prev) => prev.filter((f) => f !== file))**

                **}**

                **className="hover:text-red-400"**

              **>**

                **×**

              **</button>**

            **</span>**

          **))}**

        **</div>**

      **)}**



      **{/\* Input Area \*/}**

      **<div className="border-t border-\[#21262d] p-4">**

        **<div className="relative flex items-end gap-2">**

          **<button**

            **onClick={async () => {**

              **const file = await window.electronAPI.invoke('fs:openFile');**

              **if (file) setAttachedFiles((prev) => \[...prev, file]);**

            **}}**

            **className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-\[#161b22] transition-colors"**

          **>**

            **<Paperclip size={18} />**

          **</button>**



          **<div className="flex-1 relative">**

            **<textarea**

              **ref={inputRef}**

              **value={input}**

              **onChange={(e) => setInput(e.target.value)}**

              **onKeyDown={handleKeyDown}**

              **placeholder="Ask anything... (Shift+Enter for new line)"**

              **rows={1}**

              **className="w-full bg-\[#161b22] text-gray-200 rounded-lg px-4 py-3 pr-12 resize-none border border-\[#21262d] focus:border-blue-500 focus:outline-none placeholder-gray-500 text-sm"**

              **style={{**

                **minHeight: '44px',**

                **maxHeight: '200px',**

                **height: 'auto',**

              **}}**

              **onInput={(e) => {**

                **const target = e.target as HTMLTextAreaElement;**

                **target.style.height = 'auto';**

                **target.style.height = target.scrollHeight + 'px';**

              **}}**

            **/>**



            **<button**

              **onClick={handleSend}**

              **disabled={!input.trim() || isStreaming}**

              **className="absolute right-2 bottom-2 p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white transition-colors"**

            **>**

              **{isStreaming ? (**

                **<RefreshCw size={16} className="animate-spin" />**

              **) : (**

                **<Send size={16} />**

              **)}**

            **</button>**

          **</div>**

        **</div>**



        **<div className="flex items-center justify-between mt-2">**

          **<span className="text-\[10px] text-gray-500">**

            **{activeModel.name} • {isStreaming ? 'Generating...' : 'Ready'}**

          **</span>**

          **<span className="text-\[10px] text-gray-500">**

            **Shift+Enter for new line**

          **</span>**

        **</div>**

      **</div>**

    **</div>**

  **);**

**}**



**function MessageBubble({**

  **message,**

  **onApplyCode,**

**}: {**

  **message: Message;**

  **onApplyCode: (code: string, filePath?: string) => void;**

**}) {**

  **const \[copiedId, setCopiedId] = useState<string | null>(null);**



  **const copyToClipboard = (text: string, id: string) => {**

    **navigator.clipboard.writeText(text);**

    **setCopiedId(id);**

    **setTimeout(() => setCopiedId(null), 2000);**

  **};**



  **const isUser = message.role === 'user';**



  **return (**

    **<div className={`flex gap-3 ${isUser ? 'justify-end' : ''}`}>**

      **{!isUser \&\& (**

        **<div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0 mt-1">**

          **<Bot size={14} className="text-white" />**

        **</div>**

      **)}**



      **<div**

        **className={`max-w-\[85%] rounded-lg px-4 py-3 ${**

          **isUser**

            **? 'bg-blue-600/20 border border-blue-500/30'**

            **: 'bg-\[#161b22] border border-\[#21262d]'**

        **}`}**

      **>**

        **{isUser ? (**

          **<p className="text-sm text-gray-200 whitespace-pre-wrap">{message.content}</p>**

        **) : (**

          **<div className="prose prose-invert prose-sm max-w-none">**

            **<ReactMarkdown**

              **components={{**

                **code({ node, inline, className, children, ...props }: any) {**

                  **const match = /language-(\\w+)/.exec(className || '');**

                  **const codeString = String(children).replace(/\\n$/, '');**

                  **const blockId = `code-${message.id}-${Math.random()}`;**



                  **if (!inline \&\& match) {**

                    **return (**

                      **<div className="relative group my-2">**

                        **<div className="flex items-center justify-between px-3 py-1 bg-\[#1c2128] rounded-t-lg border border-b-0 border-\[#21262d]">**

                          **<span className="text-xs text-gray-400">{match\[1]}</span>**

                          **<div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">**

                            **<button**

                              **onClick={() => copyToClipboard(codeString, blockId)}**

                              **className="text-xs text-gray-400 hover:text-white flex items-center gap-1"**

                            **>**

                              **{copiedId === blockId ? (**

                                **<><Check size={12} /> Copied</>**

                              **) : (**

                                **<><Copy size={12} /> Copy</>**

                              **)}**

                            **</button>**

                            **<button**

                              **onClick={() => onApplyCode(codeString)}**

                              **className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"**

                            **>**

                              **Apply**

                            **</button>**

                          **</div>**

                        **</div>**

                        **<SyntaxHighlighter**

                          **style={vscDarkPlus}**

                          **language={match\[1]}**

                          **PreTag="div"**

                          **customStyle={{**

                            **margin: 0,**

                            **borderTopLeftRadius: 0,**

                            **borderTopRightRadius: 0,**

                            **border: '1px solid #21262d',**

                            **borderTop: 'none',**

                          **}}**

                          **{...props}**

                        **>**

                          **{codeString}**

                        **</SyntaxHighlighter>**

                      **</div>**

                    **);**

                  **}**



                  **return (**

                    **<code className="bg-\[#1c2128] px-1.5 py-0.5 rounded text-xs text-blue-300" {...props}>**

                      **{children}**

                    **</code>**

                  **);**

                **},**

              **}}**

            **>**

              **{message.content}**

            **</ReactMarkdown>**

            **{message.isStreaming \&\& (**

              **<span className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-1" />**

            **)}**

          **</div>**

        **)}**



        **{!isUser \&\& message.model \&\& (**

          **<div className="mt-2 text-\[10px] text-gray-500">**

            **{message.model} • {message.timestamp.toLocaleTimeString()}**

          **</div>**

        **)}**

      **</div>**



      **{isUser \&\& (**

        **<div className="w-7 h-7 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center flex-shrink-0 mt-1">**

          **<User size={14} className="text-white" />**

        **</div>**

      **)}**

    **</div>**

  **);**

**}**



**16. Backend Server (src/backend/server.ts)**



**import express from 'express';**

**import { createServer } from 'http';**

**import { Server as SocketIOServer } from 'socket.io';**

**import cors from 'cors';**

**import { AIEngine } from './ai/engine';**

**import { AgentManager } from './ai/agents/agent-manager';**

**import { DatabaseManager } from './database/db-manager';**

**import { PtyManager } from './terminal/pty-manager';**



**const app = express();**

**const httpServer = createServer(app);**

**const io = new SocketIOServer(httpServer, {**

  **cors: { origin: '\*' },**

**});**



**app.use(cors());**

**app.use(express.json({ limit: '50mb' }));**



**// Initialize services**

**const aiEngine = new AIEngine();**

**const agentManager = new AgentManager(aiEngine);**

**const dbManager = new DatabaseManager();**

**const ptyManager = new PtyManager();**



**// ===== AI Routes =====**

**app.post('/api/ai/chat', async (req, res) => {**

  **try {**

    **const response = await aiEngine.chat(req.body);**

    **res.json(response);**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.post('/api/ai/chat/stream', async (req, res) => {**

  **res.setHeader('Content-Type', 'text/event-stream');**

  **res.setHeader('Cache-Control', 'no-cache');**

  **res.setHeader('Connection', 'keep-alive');**



  **try {**

    **await aiEngine.chatStream(req.body, (chunk) => {**

      **res.write(`data: ${JSON.stringify(chunk)}\\n\\n`);**

    **});**

    **res.write('data: \[DONE]\\n\\n');**

    **res.end();**

  **} catch (error) {**

    **res.write(`data: ${JSON.stringify({ error: String(error) })}\\n\\n`);**

    **res.end();**

  **}**

**});**



**app.get('/api/ai/models', async (\_req, res) => {**

  **const models = await aiEngine.listAvailableModels();**

  **res.json(models);**

**});**



**app.post('/api/ai/complete', async (req, res) => {**

  **const { code, language, cursorPosition } = req.body;**

  **const completion = await aiEngine.generateCompletion(code, language, cursorPosition);**

  **res.json({ completion });**

**});**



**app.post('/api/ai/review', async (req, res) => {**

  **const { code, language } = req.body;**

  **const review = await aiEngine.reviewCode(code, language);**

  **res.json(review);**

**});**



**app.post('/api/ai/explain', async (req, res) => {**

  **const { code, language } = req.body;**

  **const explanation = await aiEngine.explainCode(code, language);**

  **res.json({ explanation });**

**});**



**app.post('/api/ai/refactor', async (req, res) => {**

  **const { code, language, instruction } = req.body;**

  **const refactored = await aiEngine.refactorCode(code, language, instruction);**

  **res.json({ code: refactored });**

**});**



**// ===== Agent Routes =====**

**app.get('/api/agents', (\_req, res) => {**

  **res.json(agentManager.getAllAgents());**

**});**



**app.post('/api/agents/:id/task', async (req, res) => {**

  **try {**

    **const result = await agentManager.executeTask(req.params.id, req.body);**

    **res.json({ result });**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.post('/api/agents/workflow', async (req, res) => {**

  **try {**

    **const result = await agentManager.executeWorkflow(req.body);**

    **res.json(result);**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.post('/api/agents/message', async (req, res) => {**

  **const { from, to, message } = req.body;**

  **try {**

    **const result = await agentManager.sendMessage(from, to, message);**

    **res.json({ result });**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**// ===== Database Routes =====**

**app.post('/api/db/connect', async (req, res) => {**

  **try {**

    **const id = await dbManager.connect(req.body);**

    **res.json({ connectionId: id });**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.post('/api/db/:id/query', async (req, res) => {**

  **try {**

    **const result = await dbManager.executeQuery(req.params.id, req.body.query);**

    **res.json(result);**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.get('/api/db/:id/tables', async (req, res) => {**

  **try {**

    **const tables = await dbManager.getTables(req.params.id);**

    **res.json(tables);**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.get('/api/db/:id/schema/:table', async (req, res) => {**

  **try {**

    **const schema = await dbManager.getTableSchema(req.params.id, req.params.table);**

    **res.json(schema);**

  **} catch (error) {**

    **res.status(500).json({ error: String(error) });**

  **}**

**});**



**app.get('/api/db/connections', (\_req, res) => {**

  **res.json(dbManager.getConnections());**

**});**



**// ===== WebSocket =====**

**io.on('connection', (socket) => {**

  **console.log('Client connected:', socket.id);**



  **// AI streaming via WebSocket**

  **socket.on('ai:stream', async (request) => {**

    **try {**

      **await aiEngine.chatStream(request, (chunk) => {**

        **socket.emit('ai:chunk', chunk);**

      **});**

      **socket.emit('ai:done');**

    **} catch (error) {**

      **socket.emit('ai:error', { error: String(error) });**

    **}**

  **});**



  **// Agent events**

  **agentManager.on('agent:status', (data) => {**

    **socket.emit('agent:status', data);**

  **});**



  **agentManager.on('agent:task-complete', (data) => {**

    **socket.emit('agent:task-complete', data);**

  **});**



  **agentManager.on('workflow:step-complete', (data) => {**

    **socket.emit('workflow:step-complete', data);**

  **});**



  **// Terminal via WebSocket**

  **socket.on('terminal:create', async (options, callback) => {**

    **const id = ptyManager.createTerminal(options);**



    **ptyManager.onData(id, (data) => {**

      **socket.emit(`terminal:data:${id}`, data);**

    **});**



    **ptyManager.onExit(id, (exitCode) => {**

      **socket.emit(`terminal:exit:${id}`, exitCode);**

    **});**



    **callback(id);**

  **});**



  **socket.on('terminal:input', ({ id, data }) => {**

    **ptyManager.write(id, data);**

  **});**



  **socket.on('terminal:resize', ({ id, cols, rows }) => {**

    **ptyManager.resize(id, cols, rows);**

  **});**



  **socket.on('disconnect', () => {**

    **console.log('Client disconnected:', socket.id);**

  **});**

**});**



**// Start server**

**const PORT = process.env.BACKEND\_PORT || 3001;**

**httpServer.listen(PORT, () => {**

  **console.log(`🚀 Nexus IDE Backend running on port ${PORT}`);**

**});**



**export { app, httpServer, io, aiEngine, agentManager, dbManager, ptyManager };**





**17. Docker Compose (docker-compose.yml)**



**version: '3.9'**



**services:**

  **# Ollama (Local AI)**

  **ollama:**

    **image: ollama/ollama:latest**

    **container\_name: nexus-ollama**

    **ports:**

      **- "11434:11434"**

    **volumes:**

      **- ollama-data:/root/.ollama**

    **deploy:**

      **resources:**

        **reservations:**

          **devices:**

            **- driver: nvidia**

              **count: all**

              **capabilities: \[gpu]**

    **restart: unless-stopped**



  **# PostgreSQL**

  **postgres:**

    **image: postgres:16-alpine**

    **container\_name: nexus-postgres**

    **environment:**

      **POSTGRES\_USER: nexus**

      **POSTGRES\_PASSWORD: nexus\_password**

      **POSTGRES\_DB: nexus\_db**

    **ports:**

      **- "5432:5432"**

    **volumes:**

      **- postgres-data:/var/lib/postgresql/data**

    **restart: unless-stopped**



  **# Redis (Caching \& Queue)**

  **redis:**

    **image: redis:7-alpine**

    **container\_name: nexus-redis**

    **ports:**

      **- "6379:6379"**

    **volumes:**

      **- redis-data:/data**

    **command: redis-server --appendonly yes**

    **restart: unless-stopped**



  **# MongoDB**

  **mongodb:**

    **image: mongo:7**

    **container\_name: nexus-mongodb**

    **environment:**

      **MONGO\_INITDB\_ROOT\_USERNAME: nexus**

      **MONGO\_INITDB\_ROOT\_PASSWORD: nexus\_password**

    **ports:**

      **- "27017:27017"**

    **volumes:**

      **- mongodb-data:/data/db**

    **restart: unless-stopped**



  **# ChromaDB (Vector DB for RAG)**

  **chromadb:**

    **image: chromadb/chroma:latest**

    **container\_name: nexus-chromadb**

    **ports:**

      **- "8000:8000"**

    **volumes:**

      **- chroma-data:/chroma/chroma**

    **restart: unless-stopped**



  **# MySQL (optional)**

  **mysql:**

    **image: mysql:8**

    **container\_name: nexus-mysql**

    **environment:**

      **MYSQL\_ROOT\_PASSWORD: nexus\_password**

      **MYSQL\_DATABASE: nexus\_db**

    **ports:**

      **- "3306:3306"**

    **volumes:**

      **- mysql-data:/var/lib/mysql**

    **profiles:**

      **- full**

    **restart: unless-stopped**



**volumes:**

  **ollama-data:**

  **postgres-data:**

  **redis-data:**

  **mongodb-data:**

  **chroma-data:**

  **mysql-data:**



**18. Environment Configuration (.env.example)**



**# ===== AI Provider API Keys =====**

**OPENAI\_API\_KEY=sk-...**

**ANTHROPIC\_API\_KEY=sk-ant-...**

**GOOGLE\_AI\_API\_KEY=AI...**

**DEEPSEEK\_API\_KEY=sk-...**

**GROQ\_API\_KEY=gsk\_...**

**MISTRAL\_API\_KEY=...**

**OPENROUTER\_API\_KEY=sk-or-...**

**COHERE\_API\_KEY=...**

**XAI\_API\_KEY=xai-...**



**# ===== Local AI =====**

**OLLAMA\_BASE\_URL=http://localhost:11434**

**LMSTUDIO\_BASE\_URL=http://localhost:1234**

**LLAMACPP\_BASE\_URL=http://localhost:8080**

**VLLM\_BASE\_URL=http://localhost:8000**



**# ===== Azure OpenAI =====**

**AZURE\_OPENAI\_API\_KEY=...**

**AZURE\_OPENAI\_ENDPOINT=https://your-resource.openai.azure.com**

**AZURE\_OPENAI\_API\_VERSION=2024-02-01**



**# ===== AWS Bedrock =====**

**AWS\_ACCESS\_KEY\_ID=...**

**AWS\_SECRET\_ACCESS\_KEY=...**

**AWS\_REGION=us-east-1**



**# ===== Database =====**

**POSTGRES\_URL=postgresql://nexus:nexus\_password@localhost:5432/nexus\_db**

**MONGODB\_URL=mongodb://nexus:nexus\_password@localhost:27017/nexus\_db**

**REDIS\_URL=redis://localhost:6379**

**MYSQL\_URL=mysql://root:nexus\_password@localhost:3306/nexus\_db**



**# ===== Vector DB =====**

**CHROMA\_URL=http://localhost:8000**



**# ===== App Settings =====**

**BACKEND\_PORT=3001**

**NODE\_ENV=development**

**LOG\_LEVEL=info**

**ENCRYPTION\_KEY=your-32-char-encryption-key-here**



**# ===== GitHub =====**

**GITHUB\_TOKEN=ghp\_...**



**# ===== Telemetry =====**

**TELEMETRY\_ENABLED=false**

## 

## **🚀 SETUP \& RUN SCRIPTS**

## **Setup Script (scripts/setup-local-ai.sh)**

**#!/bin/bash**



**echo "🚀 Setting up Nexus IDE Local AI Environment"**

**echo "============================================="**



**# Check for Ollama**

**if command -v ollama \&> /dev/null; then**

    **echo "✅ Ollama is installed"**

**else**

    **echo "📦 Installing Ollama..."**

    **curl -fsSL https://ollama.ai/install.sh | sh**

**fi**



**# Pull recommended models**

**echo ""**

**echo "📥 Pulling recommended AI models..."**



**echo "  → Pulling CodeLlama 13B (for code generation)..."**

**ollama pull codellama:13b**



**echo "  → Pulling DeepSeek Coder V2 (for advanced coding)..."**

**ollama pull deepseek-coder-v2:16b**



**echo "  → Pulling Llama 3.1 8B (for general tasks)..."**

**ollama pull llama3.1:8b**



**echo "  → Pulling Nomic Embed (for code embeddings)..."**

**ollama pull nomic-embed-text**



**echo "  → Pulling StarCoder2 (for completions)..."**

**ollama pull starcoder2:7b**



**echo ""**

**echo "✅ Local AI setup complete!"**

**echo ""**

**echo "Available models:"**

**ollama list**



**echo ""**

**echo "🐳 Starting Docker services..."**

**docker-compose up -d**



**echo ""**

**echo "✅ All services are running!"**

**echo ""**

**echo "Next steps:"**

**echo "  1. Copy .env.example to .env and add your API keys"**

**echo "  2. Run 'npm install'"**

**echo "  3. Run 'npm run dev'"**



## **📋 BUILD \& RUN COMMANDS**

**# Initial Setup**

**git clone https://github.com/your-org/nexus-ide.git**

**cd nexus-ide**

**cp .env.example .env**

**# Edit .env with your API keys**



**# Install dependencies**

**npm install**



**# Setup local AI (Ollama + Docker services)**

**chmod +x scripts/setup-local-ai.sh**

**./scripts/setup-local-ai.sh**



**# Development**

**npm run dev**



**# Build for production**

**npm run build**



**# Build for specific platforms**

**npm run build:mac**

**npm run build:win**

**npm run build:linux**



**# Run tests**

**npm run test**

**npm run test:e2e**



**# Lint and type check**

**npm run lint**

**npm run typecheck**



### **🏗️ KEY ARCHITECTURAL FEATURES**



**┌─────────────────────────────────────────────────────────────────┐**

**│                        NEXUS IDE ARCHITECTURE                    │**

**├─────────────────────────────────────────────────────────────────┤**

**│                                                                  │**

**│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐   │**

**│  │ Electron  │  │   React +    │  │    Monaco Editor        │   │**

**│  │  Main     │←→│   Renderer   │←→│  (Code + Diff + Mini)   │   │**

**│  │ Process   │  │  (Frontend)  │  │                         │   │**

**│  └─────┬────┘  └──────┬───────┘  └─────────────────────────┘   │**

**│        │               │                                         │**

**│        │         IPC Bridge                                      │**

**│        │               │                                         │**

**│  ┌─────▼───────────────▼─────────────────────────────────────┐  │**

**│  │                    BACKEND SERVER                          │  │**

**│  │  ┌─────────────────────────────────────────────────┐      │  │**

**│  │  │              AI ENGINE CORE                      │      │  │**

**│  │  │  ┌─────────┐  ┌──────────┐  ┌──────────────┐   │      │  │**

**│  │  │  │ Context  │  │  Token   │  │   Prompt     │   │      │  │**

**│  │  │  │ Manager  │  │ Counter  │  │   Builder    │   │      │  │**

**│  │  │  └─────────┘  └──────────┘  └──────────────┘   │      │  │**

**│  │  │                                                  │      │  │**

**│  │  │  ┌──────────────────────────────────────────┐   │      │  │**

**│  │  │  │          AI PROVIDERS                     │   │      │  │**

**│  │  │  │  ┌────────┐ ┌──────────┐ ┌────────────┐  │   │      │  │**

**│  │  │  │  │ OpenAI │ │Anthropic │ │  Google AI  │  │   │      │  │**

**│  │  │  │  └────────┘ └──────────┘ └────────────┘  │   │      │  │**

**│  │  │  │  ┌────────┐ ┌──────────┐ ┌────────────┐  │   │      │  │**

**│  │  │  │  │DeepSeek│ │  Groq    │ │ OpenRouter  │  │   │      │  │**

**│  │  │  │  └────────┘ └──────────┘ └────────────┘  │   │      │  │**

**│  │  │  │  ┌────────┐ ┌──────────┐ ┌────────────┐  │   │      │  │**

**│  │  │  │  │ Ollama │ │LM Studio │ │  llama.cpp  │  │   │      │  │**

**│  │  │  │  │(LOCAL) │ │ (LOCAL)  │ │  (LOCAL)    │  │   │      │  │**

**│  │  │  │  └────────┘ └──────────┘ └────────────┘  │   │      │  │**

**│  │  │  └──────────────────────────────────────────┘   │      │  │**

**│  │  │                                                  │      │  │**

**│  │  │  ┌──────────────────────────────────────────┐   │      │  │**

**│  │  │  │        MULTI-AGENT SYSTEM                 │   │      │  │**

**│  │  │  │  🏗️ Architect  │  💻 Coder  │ 🔍 Reviewer │   │      │  │**

**│  │  │  │  🐛 Debugger   │  🧪 Tester │ 🔒 Security │   │      │  │**

**│  │  │  │  📝 Docs       │  🚀 DevOps │ 💬 Terminal  │   │      │  │**

**│  │  │  │  🔬 Research   │  🎨 UI     │ ⚡ Perf      │   │      │  │**

**│  │  │  │                                           │   │      │  │**

**│  │  │  │  Workflows: Sequential │ Parallel │       │   │      │  │**

**│  │  │  │             Hierarchical │ Consensus      │   │      │  │**

**│  │  │  └──────────────────────────────────────────┘   │      │  │**

**│  │  └─────────────────────────────────────────────────┘      │  │**

**│  │                                                            │  │**

**│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐             │  │**

**│  │  │ Terminal   │  │   Git     │  │ Database  │             │  │**

**│  │  │ (node-pty) │  │ (isogit) │  │ Manager   │             │  │**

**│  │  └───────────┘  └───────────┘  └───────────┘             │  │**

**│  │                                                            │  │**

**│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐             │  │**

**│  │  │   LSP     │  │ Extension │  │  Vector   │             │  │**

**│  │  │ Manager   │  │   Host    │  │   DB/RAG  │             │  │**

**│  │  └───────────┘  └───────────┘  └───────────┘             │  │**

**│  └────────────────────────────────────────────────────────────┘  │**

**│                                                                  │**

**│  ┌────────────────────────────────────────────────────────────┐  │**

**│  │                    DATA LAYER                               │  │**

**│  │  ┌────────┐ ┌──────────┐ ┌───────┐ ┌───────┐ ┌────────┐  │  │**

**│  │  │ SQLite │ │PostgreSQL│ │ MySQL │ │MongoDB│ │ Redis  │  │  │**

**│  │  └────────┘ └──────────┘ └───────┘ └───────┘ └────────┘  │  │**

**│  │  ┌────────┐ ┌──────────┐                                  │  │**

**│  │  │DuckDB  │ │ ChromaDB │                                  │  │**

**│  │  └────────┘ └──────────┘                                  │  │**

**│  └────────────────────────────────────────────────────────────┘  │**

**└─────────────────────────────────────────────────────────────────┘**



### **✅ FEATURE CHECKLIST**

**EDITOR**

  **✅ Monaco Editor with full LSP support**

  **✅ Multi-tab editing with split panes**

  **✅ AI-powered autocomplete (inline ghost text)**

  **✅ Syntax highlighting (Tree-sitter)**

  **✅ Code minimap**

  **✅ Breadcrumb navigation**

  **✅ Diff viewer**

  **✅ Multi-cursor editing**

  **✅ Code folding**

  **✅ Find and replace (regex)**



**AI FEATURES**

  **✅ Chat interface with streaming**

  **✅ 15+ AI model providers (cloud + local)**

  **✅ Ollama integration (fully local)**

  **✅ LM Studio integration**

  **✅ OpenCode integration**

  **✅ AI code completion**

  **✅ AI code review**

  **✅ AI code explanation**

  **✅ AI refactoring**

  **✅ AI test generation**

  **✅ Context-aware (RAG with codebase)**

  **✅ Cost tracking per model**



**MULTI-AGENT SYSTEM**

  **✅ 15 specialized agents**

  **✅ Agent orchestration (sequential, parallel, hierarchical, consensus)**

  **✅ Inter-agent communication**

  **✅ Agent memory (vector store)**

  **✅ Agent tools (file, terminal, browser, git, DB)**

  **✅ Visual workflow builder**

  **✅ Task queue (BullMQ)**



**TERMINAL**

  **✅ Full PTY terminal (node-pty + xterm.js)**

  **✅ Multiple terminal instances**

  **✅ Shell selection (bash, zsh, fish, PowerShell)**

  **✅ WebGL rendering for performance**

  **✅ Search in terminal**

  **✅ Clickable links**

  **✅ AI-suggested commands**



**FILE SYSTEM**

  **✅ File tree explorer**

  **✅ File watching (chokidar)**

  **✅ Fast search (ripgrep)**

  **✅ Drag and drop**

  **✅ Git status indicators**

  **✅ Workspace management**



**DATABASE**

  **✅ SQLite, PostgreSQL, MySQL, MongoDB, Redis, DuckDB**

  **✅ Query editor with syntax highlighting**

  **✅ Table data viewer**

  **✅ Schema visualizer**

  **✅ Connection manager**

  **✅ Query history**



**GIT**

  **✅ Status, commit, push, pull**

  **✅ Branch management**

  **✅ Diff viewer**

  **✅ Merge conflict resolver**

  **✅ Visual git graph**

  **✅ GitHub/GitLab integration**



**EXTENSIONS**

  **✅ Extension marketplace**

  **✅ VSCode extension compatibility layer**

  **✅ Sandboxed extension runtime**

  **✅ Built-in extensions**



**UI/UX**

  **✅ Dark/Light themes + custom themes**

  **✅ Resizable panels (react-resizable-panels)**

  **✅ Command palette (Ctrl+Shift+P)**

  **✅ Keyboard shortcuts**

  **✅ Status bar**

  **✅ Activity bar**

  **✅ Toast notifications**

  **✅ Responsive layout**



### **To build this, start with:**

**npm init → Set up the project with the package.json above**

**Implement the Electron main process**

**Build the React renderer with Monaco Editor**

**Wire up the AI Engine with providers**

**Implement the terminal with node-pty**

**Add the multi-agent system**

**Connect databases**

**Polish the UI**
















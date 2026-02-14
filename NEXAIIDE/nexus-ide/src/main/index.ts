import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import path from 'path';

class NexusIDE {
  private mainWindow: BrowserWindow | null = null;

  constructor() {
    this.initialize();
  }

  private async initialize() {
    await app.whenReady();

    // Create main window
    this.createMainWindow();

    // Handle app lifecycle
    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') app.quit();
    });

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createMainWindow();
      }
    });

    // Single instance lock
    const gotTheLock = app.requestSingleInstanceLock();
    if (!gotTheLock) {
      app.quit();
    } else {
      app.on('second-instance', (_event, commandLine) => {
        if (this.mainWindow) {
          if (this.mainWindow.isMinimized()) this.mainWindow.restore();
          this.mainWindow.focus();
          const filePath = commandLine[commandLine.length - 1];
          if (filePath && !filePath.startsWith('--')) {
            this.mainWindow.webContents.send('open-file', filePath);
          }
        }
      });
    }
  }

  private createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1600,
      height: 1000,
      minWidth: 1024,
      minHeight: 768,
      title: 'Nexus IDE',
      backgroundColor: '#0d1117',
      show: false,
      frame: true,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: false,
        webviewTag: true,
        spellcheck: true,
      },
    });

    // Load renderer
    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:5173');
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
    }

    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.maximize();
      this.mainWindow?.show();
      this.mainWindow?.focus();
    });

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    // Register IPC handlers
    this.registerIpcHandlers();

    return this.mainWindow;
  }

  private registerIpcHandlers() {
    const fs = require('fs');
    const pathModule = require('path');

    // ===== FILE SYSTEM =====
    ipcMain.handle('fs:readDir', async (_event, dirPath: string) => {
      try {
        const entries = fs.readdirSync(dirPath, { withFileTypes: true });
        return entries.map((entry: any) => ({
          name: entry.name,
          path: pathModule.join(dirPath, entry.name),
          type: entry.isDirectory() ? 'directory' : 'file',
          extension: entry.isFile() ? pathModule.extname(entry.name) : undefined,
        })).sort((a: any, b: any) => {
          if (a.type === b.type) return a.name.localeCompare(b.name);
          return a.type === 'directory' ? -1 : 1;
        });
      } catch {
        return [];
      }
    });

    ipcMain.handle('fs:readFile', async (_event, filePath: string) => {
      try {
        return fs.readFileSync(filePath, 'utf-8');
      } catch (err: any) {
        throw new Error(`Failed to read file: ${err.message}`);
      }
    });

    ipcMain.handle('fs:writeFile', async (_event, filePath: string, content: string) => {
      try {
        fs.writeFileSync(filePath, content, 'utf-8');
        return true;
      } catch (err: any) {
        throw new Error(`Failed to write file: ${err.message}`);
      }
    });

    ipcMain.handle('fs:createFile', async (_event, filePath: string) => {
      try {
        const dir = pathModule.dirname(filePath);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(filePath, '', 'utf-8');
        return true;
      } catch (err: any) {
        throw new Error(`Failed to create file: ${err.message}`);
      }
    });

    ipcMain.handle('fs:createDir', async (_event, dirPath: string) => {
      try {
        fs.mkdirSync(dirPath, { recursive: true });
        return true;
      } catch (err: any) {
        throw new Error(`Failed to create directory: ${err.message}`);
      }
    });

    ipcMain.handle('fs:delete', async (_event, targetPath: string) => {
      try {
        fs.rmSync(targetPath, { recursive: true, force: true });
        return true;
      } catch (err: any) {
        throw new Error(`Failed to delete: ${err.message}`);
      }
    });

    ipcMain.handle('fs:rename', async (_event, oldPath: string, newPath: string) => {
      try {
        fs.renameSync(oldPath, newPath);
        return true;
      } catch (err: any) {
        throw new Error(`Failed to rename: ${err.message}`);
      }
    });

    ipcMain.handle('fs:stat', async (_event, targetPath: string) => {
      try {
        const stat = fs.statSync(targetPath);
        return {
          size: stat.size,
          modified: stat.mtime,
          created: stat.birthtime,
          isDirectory: stat.isDirectory(),
          isFile: stat.isFile(),
        };
      } catch {
        return null;
      }
    });

    // ===== DIALOG =====
    const { dialog, shell, clipboard } = require('electron');

    ipcMain.handle('dialog:openFolder', async () => {
      const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
      return result.canceled ? null : result.filePaths[0];
    });

    ipcMain.handle('dialog:openFile', async () => {
      const result = await dialog.showOpenDialog({ properties: ['openFile'] });
      return result.canceled ? null : result.filePaths[0];
    });

    // ===== SHELL =====
    ipcMain.handle('shell:openExternal', async (_event, url: string) => {
      return shell.openExternal(url);
    });

    ipcMain.handle('shell:showItemInFolder', async (_event, filePath: string) => {
      shell.showItemInFolder(filePath);
    });

    // ===== CLIPBOARD =====
    ipcMain.handle('clipboard:read', async () => clipboard.readText());
    ipcMain.handle('clipboard:write', async (_event, text: string) => clipboard.writeText(text));

    // ===== APP INFO =====
    ipcMain.handle('app:getVersion', async () => app.getVersion());
    ipcMain.handle('app:getPlatform', async () => process.platform);
  }
}

new NexusIDE();

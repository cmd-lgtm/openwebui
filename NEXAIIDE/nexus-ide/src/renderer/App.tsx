import React from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { Toaster } from 'sonner';

declare global {
  interface Window {
    electronAPI: {
      invoke: (channel: string, ...args: unknown[]) => Promise<unknown>;
      on: (channel: string, callback: (...args: unknown[]) => void) => () => void;
      send: (channel: string, ...args: unknown[]) => void;
      removeAllListeners: (channel: string) => void;
      fs: {
        readDir: (dirPath: string) => Promise<any[]>;
        readFile: (filePath: string) => Promise<string>;
        writeFile: (filePath: string, content: string) => Promise<boolean>;
        createFile: (filePath: string) => Promise<boolean>;
        createDir: (dirPath: string) => Promise<boolean>;
        delete: (targetPath: string) => Promise<boolean>;
        rename: (oldPath: string, newPath: string) => Promise<boolean>;
        stat: (targetPath: string) => Promise<any>;
      };
      dialog: {
        openFolder: () => Promise<string | null>;
        openFile: () => Promise<string | null>;
      };
      shell: {
        openExternal: (url: string) => Promise<void>;
        showItemInFolder: (filePath: string) => Promise<void>;
      };
      clipboard: {
        read: () => Promise<string>;
        write: (text: string) => Promise<void>;
      };
      app: {
        getVersion: () => Promise<string>;
        getPlatform: () => Promise<string>;
      };
    };
  }
}

export default function App() {
  return (
    <>
      <MainLayout />
      <Toaster
        position="bottom-right"
        theme="dark"
        toastOptions={{
          style: {
            background: '#161b22',
            border: '1px solid #30363d',
            color: '#e6edf3',
            fontFamily: 'Inter, system-ui, sans-serif',
          },
        }}
      />
    </>
  );
}

// ===== Database Types =====

export type DatabaseDriver = 'sqlite' | 'postgresql' | 'mysql' | 'mongodb' | 'redis' | 'duckdb';

export interface DatabaseConnection {
  id: string;
  name: string;
  driver: DatabaseDriver;
  host?: string;
  port?: number;
  database: string;
  username?: string;
  password?: string;
  url?: string;
  isConnected: boolean;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  executionTime: number;
  error?: string;
}

export interface TableInfo {
  name: string;
  schema?: string;
  rowCount?: number;
  columns: ColumnInfo[];
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primaryKey: boolean;
  defaultValue?: string;
  foreignKey?: { table: string; column: string };
}

export interface QueryHistoryEntry {
  id: string;
  query: string;
  connectionId: string;
  executedAt: Date;
  duration: number;
  rowCount?: number;
  error?: string;
}

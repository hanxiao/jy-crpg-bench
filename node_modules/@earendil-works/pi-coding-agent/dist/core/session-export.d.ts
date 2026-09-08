import { type SessionManager } from "./session-manager.ts";
/** Write the current session branch and optional trailing export-only entries as JSONL. */
export declare function exportSessionToJsonl(sessionManager: SessionManager, outputPath?: string, createTrailingEntries?: (parentId: string | null, timestamp: string) => readonly object[]): string;
//# sourceMappingURL=session-export.d.ts.map
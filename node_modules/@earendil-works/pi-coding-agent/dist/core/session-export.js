import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { resolvePath } from "../utils/paths.js";
import { CURRENT_SESSION_VERSION } from "./session-manager.js";
/** Write the current session branch and optional trailing export-only entries as JSONL. */
export function exportSessionToJsonl(sessionManager, outputPath, createTrailingEntries) {
    const filePath = resolvePath(outputPath ?? `session-${new Date().toISOString().replace(/[:.]/g, "-")}.jsonl`, process.cwd());
    const dir = dirname(filePath);
    if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
    }
    const timestamp = new Date().toISOString();
    const header = {
        type: "session",
        version: CURRENT_SESSION_VERSION,
        id: sessionManager.getSessionId(),
        timestamp,
        cwd: sessionManager.getCwd(),
    };
    const lines = [JSON.stringify(header)];
    let parentId = null;
    for (const entry of sessionManager.getBranch()) {
        lines.push(JSON.stringify({ ...entry, parentId }));
        parentId = entry.id;
    }
    for (const entry of createTrailingEntries?.(parentId, timestamp) ?? []) {
        lines.push(JSON.stringify(entry));
    }
    writeFileSync(filePath, `${lines.join("\n")}\n`);
    return filePath;
}
//# sourceMappingURL=session-export.js.map
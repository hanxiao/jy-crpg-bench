import { type Container, type EditorComponent, type TUI } from "@earendil-works/pi-tui";
import type { AgentSession } from "../../core/agent-session.ts";
interface SessionShareContext {
    session: AgentSession;
    ui: TUI;
    editorContainer: Container;
    editor: EditorComponent;
    showStatus: (message: string) => void;
    showError: (message: string) => void;
}
/** Export the current branch with presentation metadata for Radius. */
export declare function exportSessionForShare(filePath: string, session: AgentSession): void;
/** Share the current session through Radius, falling back to a private gist. */
export declare function shareSession(context: SessionShareContext): Promise<void>;
export {};
//# sourceMappingURL=session-share.d.ts.map
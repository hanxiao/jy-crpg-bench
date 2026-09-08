import type { CommandResult, ServerEvent, ServerSnapshot, SessionSnapshot } from "@earendil-works/pi-protocol";
import type { ListenerErrorHandler, Unsubscribe } from "./types.ts";
export declare class ClientState {
    #private;
    constructor(onListenerError?: ListenerErrorHandler);
    get snapshot(): ServerSnapshot | undefined;
    reset(): void;
    clearAttachments(): void;
    dispose(): void;
    getSessionSnapshot(sessionId: string): SessionSnapshot | undefined;
    isSessionAttached(sessionId: string): boolean;
    forgetSessionSnapshot(sessionId: string): SessionSnapshot | undefined;
    restoreSessionSnapshot(snapshot: SessionSnapshot): void;
    subscribe(listener: (snapshot: ServerSnapshot) => void): Unsubscribe;
    onEvent(listener: (event: ServerEvent) => void): Unsubscribe;
    subscribeSession(sessionId: string, listener: (snapshot: SessionSnapshot) => void): Unsubscribe;
    onSessionEvent(sessionId: string, listener: (event: ServerEvent) => void): Unsubscribe;
    applyResult(result: CommandResult): void;
    applyEvent(event: ServerEvent): void;
    applyServerSnapshot(snapshot: ServerSnapshot): void;
}
//# sourceMappingURL=state.d.ts.map
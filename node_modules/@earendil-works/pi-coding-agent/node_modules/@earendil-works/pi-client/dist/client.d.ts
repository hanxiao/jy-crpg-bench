import { type ServerEvent, type ServerSnapshot, type SessionMetadata } from "@earendil-works/pi-protocol";
import { type AcquireSessionOptions, type PiSessionHandle } from "./session-handle.ts";
import type { ConnectionState, ConnectionStateChange, CreateSessionOptions, PiClientOptions, Unsubscribe } from "./types.ts";
export declare class PiClient {
    #private;
    constructor(options: PiClientOptions);
    get disposed(): boolean;
    get connectionState(): ConnectionState;
    get connected(): boolean;
    get snapshot(): ServerSnapshot | undefined;
    static connect(options: PiClientOptions): Promise<PiClient>;
    connect(): Promise<ServerSnapshot>;
    reconnect(): Promise<ServerSnapshot>;
    disconnect(reason?: string): void;
    subscribe(listener: (snapshot: ServerSnapshot) => void): Unsubscribe;
    onEvent(listener: (event: ServerEvent) => void): Unsubscribe;
    onConnectionStateChange(listener: (change: ConnectionStateChange) => void): Unsubscribe;
    listSessions(): Promise<readonly SessionMetadata[]>;
    createSession(options?: CreateSessionOptions): Promise<PiSessionHandle>;
    attachSession(sessionId: string): Promise<PiSessionHandle>;
    acquireSession(sessionId: string, options: AcquireSessionOptions): Promise<PiSessionHandle>;
    dispose(): Promise<void>;
    [Symbol.asyncDispose](): Promise<void>;
}
//# sourceMappingURL=client.d.ts.map
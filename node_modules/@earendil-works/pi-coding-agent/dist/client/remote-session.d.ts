import type { ConnectionState, ConnectionStateChange, PiClient, Unsubscribe } from "@earendil-works/pi-client";
import type { ModelMetadata, ModelRef, SessionMetadata, SessionPhase, SessionSnapshot, ThinkingLevel, TranscriptItem } from "@earendil-works/pi-protocol";
export type RemoteSessionOperation = "open" | "create" | "submit" | "abort" | "setModel" | "setThinking" | "reconnect";
export type RemoteSessionLifecycle = {
    readonly status: "unbound";
} | {
    readonly status: "ready";
} | {
    readonly status: "busy";
    readonly operation: RemoteSessionOperation;
} | {
    readonly status: "disposed";
};
export interface RemoteSessionState {
    readonly lifecycle: RemoteSessionLifecycle;
    readonly snapshot?: SessionSnapshot;
    readonly transcript: readonly TranscriptItem[];
}
export interface CreateRemoteSessionOptions {
    cwd: string;
    model?: ModelRef;
    thinkingLevel?: ThinkingLevel;
}
export interface RemoteSessionOptions {
    onListenerError?: (error: Error) => void;
}
export declare class RemoteSession {
    #private;
    private constructor();
    get id(): string | undefined;
    get state(): RemoteSessionState;
    get snapshot(): SessionSnapshot | undefined;
    get phase(): SessionPhase | undefined;
    get operation(): RemoteSessionOperation | undefined;
    get models(): readonly ModelMetadata[];
    get sessions(): readonly SessionMetadata[];
    get connectionState(): ConnectionState;
    get disposed(): boolean;
    subscribe(listener: (state: RemoteSessionState) => void): Unsubscribe;
    onConnectionStateChange(listener: (change: ConnectionStateChange) => void): Unsubscribe;
    static open(client: PiClient, sessionId: string, options?: RemoteSessionOptions): Promise<RemoteSession>;
    open(sessionId: string): Promise<void>;
    static create(client: PiClient, createOptions: CreateRemoteSessionOptions, options?: RemoteSessionOptions): Promise<RemoteSession>;
    create(options: CreateRemoteSessionOptions): Promise<void>;
    submit(text: string): Promise<void>;
    abort(): Promise<void>;
    setModel(model: ModelRef): Promise<void>;
    setThinking(thinkingLevel: ThinkingLevel): Promise<void>;
    reconnect(): Promise<void>;
    dispose(): Promise<void>;
    [Symbol.asyncDispose](): Promise<void>;
}
//# sourceMappingURL=remote-session.d.ts.map
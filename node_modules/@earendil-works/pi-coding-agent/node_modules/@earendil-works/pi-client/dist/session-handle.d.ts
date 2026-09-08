import type { Command, ModelRef, ResultForCommand, ServerEvent, SessionSnapshot, ThinkingLevel } from "@earendil-works/pi-protocol";
import type { Unsubscribe } from "./types.ts";
type SessionCommand = Extract<Command, {
    sessionId: string;
}>;
export type SessionLeaseMode = "shared" | "exclusive";
export interface AcquireSessionOptions {
    mode: SessionLeaseMode;
}
export interface SessionLease extends AsyncDisposable {
    readonly id: string;
    readonly active: boolean;
    readonly attached: boolean;
    readonly snapshot: SessionSnapshot | undefined;
    subscribe(listener: (snapshot: SessionSnapshot) => void): Unsubscribe;
    onEvent(listener: (event: ServerEvent) => void): Unsubscribe;
    detach(): Promise<void>;
    dispose(): Promise<void>;
    prompt(text: string): Promise<SessionSnapshot>;
    steer(text: string): Promise<SessionSnapshot>;
    abort(): Promise<SessionSnapshot>;
    setModel(model: ModelRef): Promise<SessionSnapshot>;
    setThinking(thinkingLevel: ThinkingLevel): Promise<SessionSnapshot>;
}
export type PiSessionHandle = SessionLease;
export interface SessionHandleCallbacks {
    isAttached(): boolean;
    getSnapshot(): SessionSnapshot | undefined;
    subscribe(listener: (snapshot: SessionSnapshot) => void): Unsubscribe;
    onEvent(listener: (event: ServerEvent) => void): Unsubscribe;
    detach(): Promise<void>;
    dispose(): Promise<void>;
    request<const TCommand extends SessionCommand>(command: TCommand): Promise<ResultForCommand<TCommand>>;
}
export declare class SessionHandle implements SessionLease {
    #private;
    readonly id: string;
    constructor(id: string, callbacks: SessionHandleCallbacks);
    get attached(): boolean;
    get active(): boolean;
    get snapshot(): SessionSnapshot | undefined;
    subscribe(listener: (snapshot: SessionSnapshot) => void): Unsubscribe;
    onEvent(listener: (event: ServerEvent) => void): Unsubscribe;
    detach(): Promise<void>;
    dispose(): Promise<void>;
    [Symbol.asyncDispose](): Promise<void>;
    prompt(text: string): Promise<SessionSnapshot>;
    steer(text: string): Promise<SessionSnapshot>;
    abort(): Promise<SessionSnapshot>;
    setModel(model: ModelRef): Promise<SessionSnapshot>;
    setThinking(thinkingLevel: ThinkingLevel): Promise<SessionSnapshot>;
}
export {};
//# sourceMappingURL=session-handle.d.ts.map
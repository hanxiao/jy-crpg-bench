import type { JsonValue, ProtocolError, ProtocolErrorCode } from "@earendil-works/pi-protocol";
export declare class PiServerError extends Error {
    readonly code: ProtocolErrorCode;
    readonly details: JsonValue | undefined;
    constructor(error: ProtocolError);
}
export declare class PiDisconnectedError extends Error {
    constructor(message?: string);
}
export declare class PiClientDisposedError extends Error {
    constructor();
}
export declare class PiSessionOwnershipError extends Error {
    readonly sessionId: string;
    constructor(sessionId: string, message: string);
}
export declare class PiSessionDetachedError extends Error {
    readonly sessionId: string;
    constructor(sessionId: string);
}
export declare function toError(error: unknown): Error;
export declare function toDisconnectedError(error: unknown): PiDisconnectedError;
//# sourceMappingURL=errors.d.ts.map
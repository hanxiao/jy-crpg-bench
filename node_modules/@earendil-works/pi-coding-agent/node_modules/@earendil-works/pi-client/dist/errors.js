export class PiServerError extends Error {
    code;
    details;
    constructor(error) {
        super(error.message);
        this.name = "PiServerError";
        this.code = error.code;
        this.details = error.details;
    }
}
export class PiDisconnectedError extends Error {
    constructor(message = "Pi client is disconnected") {
        super(message);
        this.name = "PiDisconnectedError";
    }
}
export class PiClientDisposedError extends Error {
    constructor() {
        super("Pi client is disposed");
        this.name = "PiClientDisposedError";
    }
}
export class PiSessionOwnershipError extends Error {
    sessionId;
    constructor(sessionId, message) {
        super(message);
        this.name = "PiSessionOwnershipError";
        this.sessionId = sessionId;
    }
}
export class PiSessionDetachedError extends Error {
    sessionId;
    constructor(sessionId) {
        super(`Session ${sessionId} is not attached`);
        this.name = "PiSessionDetachedError";
        this.sessionId = sessionId;
    }
}
export function toError(error) {
    return error instanceof Error ? error : new Error(String(error));
}
export function toDisconnectedError(error) {
    const cause = toError(error);
    return cause instanceof PiDisconnectedError ? cause : new PiDisconnectedError(cause.message);
}
//# sourceMappingURL=errors.js.map
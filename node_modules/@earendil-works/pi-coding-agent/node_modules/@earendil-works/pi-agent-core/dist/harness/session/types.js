import "../messages.js";
export class SessionError extends Error {
    code;
    constructor(code, message, cause) {
        super(message, cause === undefined ? undefined : { cause });
        this.name = "SessionError";
        this.code = code;
    }
}
//# sourceMappingURL=types.js.map
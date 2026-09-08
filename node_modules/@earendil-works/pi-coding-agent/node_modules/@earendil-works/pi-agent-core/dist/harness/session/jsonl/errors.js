import { SessionError } from "../types.js";
export class JsonlDecodeError extends Error {
    kind;
    constructor(kind, message, cause) {
        super(message, cause === undefined ? undefined : { cause });
        this.name = "JsonlDecodeError";
        this.kind = kind;
    }
}
export function fileResult(result, message) {
    if (!result.ok) {
        throw new SessionError(result.error.code === "not_found" ? "not_found" : "storage", `${message}: ${result.error.message}`, result.error);
    }
    return result.value;
}
export function invalidFile(path, line, cause) {
    return new SessionError("invalid_entry", `Invalid JSONL v4 session ${path}: line ${line} ${cause.message}`, cause);
}
//# sourceMappingURL=errors.js.map
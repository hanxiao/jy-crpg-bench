import type { FileError, Result } from "../../types.ts";
import { SessionError } from "../types.ts";
export declare class JsonlDecodeError extends Error {
    readonly kind: "syntax" | "schema";
    constructor(kind: "syntax" | "schema", message: string, cause?: Error);
}
export declare function fileResult<T>(result: Result<T, FileError>, message: string): T;
export declare function invalidFile(path: string, line: number, cause: Error): SessionError;
//# sourceMappingURL=errors.d.ts.map
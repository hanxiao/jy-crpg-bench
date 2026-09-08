import { type Result } from "../../types.ts";
import type { SessionMutation } from "../state.ts";
import { JsonlDecodeError } from "./errors.ts";
import type { JsonlSessionMetadata, JsonlV4Header } from "./types.ts";
export declare function parseHeader(line: string): Result<JsonlV4Header, JsonlDecodeError>;
export declare function encodeHeader(header: JsonlV4Header): string;
export declare function metadataFromHeader(header: JsonlV4Header, path: string, modifiedAt: number): JsonlSessionMetadata;
export declare function parseMutation(line: string): Result<SessionMutation, JsonlDecodeError>;
export declare function encodeMutation(mutation: SessionMutation): string;
//# sourceMappingURL=codec.d.ts.map
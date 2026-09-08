export declare const UINT32_BASE = 4294967296;
export declare const MAX_UINT32 = 4294967295;
/** Safe defaults for untrusted protocol payloads. */
export declare const DEFAULT_MAX_CBOR_BYTE_LENGTH: number;
export declare const DEFAULT_MAX_CBOR_CONTAINER_LENGTH = 1000000;
export declare const DEFAULT_MAX_CBOR_DEPTH = 64;
export interface CborOptions {
    /** Maximum encoded input/output bytes and maximum byte/text string length. */
    maxByteLength?: number;
    /** Maximum number of elements in an array or entries in a map. */
    maxContainerLength?: number;
    /** Maximum recursive item depth. */
    maxDepth?: number;
}
export interface ResolvedCborOptions {
    maxByteLength: number;
    maxContainerLength: number;
    maxDepth: number;
}
export declare class CborError extends Error {
    constructor(message: string);
}
export declare const textEncoder: import("util").TextEncoder;
export declare const textDecoder: import("util").TextDecoder;
export declare function resolveOptions(options: CborOptions | undefined): ResolvedCborOptions;
//# sourceMappingURL=options.d.ts.map
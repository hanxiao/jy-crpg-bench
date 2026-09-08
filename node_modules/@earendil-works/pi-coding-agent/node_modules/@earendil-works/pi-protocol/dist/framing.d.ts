/** Default upper bound for one framed CBOR payload. */
export declare const DEFAULT_MAX_FRAME_LENGTH: number;
export interface FrameDecoderOptions {
    maxFrameLength?: number;
}
export declare class FrameError extends Error {
    constructor(message: string);
}
/** Prefixes a payload with its unsigned 32-bit big-endian byte length. */
export declare function encodeFrame(payload: Uint8Array): Uint8Array;
/** Validates that bytes contain exactly one complete frame within the configured limit. */
export declare function assertCompleteFrame(frame: Uint8Array, options?: FrameDecoderOptions): void;
/** Incrementally splits arbitrary byte chunks into length-prefixed payloads. */
export declare class FrameDecoder {
    private readonly header;
    private headerLength;
    private readonly maxFrameLength;
    private payloadBlocks;
    private currentPayloadBlock;
    private currentPayloadBlockLength;
    private expectedPayloadLength;
    private payloadLength;
    private state;
    constructor(options?: FrameDecoderOptions);
    push(chunk: Uint8Array): Uint8Array[];
    end(): void;
    private fail;
}
//# sourceMappingURL=framing.d.ts.map
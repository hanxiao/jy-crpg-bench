import { type FrameDecoderOptions } from "./framing.ts";
import { type ClientMessage, PROTOCOL_VERSION, type ServerMessage } from "./schemas.ts";
export declare class ProtocolValidationError extends Error {
    constructor(message: string, _value?: unknown);
}
export declare function parseClientMessage(value: unknown): ClientMessage;
export declare function parseServerMessage(value: unknown): ServerMessage;
/** Validates and encodes one complete length-prefixed client message. */
export declare function encodeClientMessage(message: ClientMessage, options?: FrameDecoderOptions): Uint8Array;
/** Validates and encodes one complete length-prefixed server message. */
export declare function encodeServerMessage(message: ServerMessage, options?: FrameDecoderOptions): Uint8Array;
/** Incrementally decodes and validates framed client messages. */
export declare class ClientMessageDecoder {
    private readonly decoder;
    constructor(options?: FrameDecoderOptions);
    push(chunk: Uint8Array): ClientMessage[];
    end(): void;
}
/** Incrementally decodes and validates framed server messages. */
export declare class ServerMessageDecoder {
    private readonly decoder;
    constructor(options?: FrameDecoderOptions);
    push(chunk: Uint8Array): ServerMessage[];
    end(): void;
}
export declare function createClientMessageDecoder(options?: FrameDecoderOptions): ClientMessageDecoder;
export declare function createServerMessageDecoder(options?: FrameDecoderOptions): ServerMessageDecoder;
export declare function isSupportedProtocolVersion(version: number): version is typeof PROTOCOL_VERSION;
//# sourceMappingURL=codec.d.ts.map
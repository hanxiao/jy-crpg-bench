import type { ByteTransportFactory } from "./transport.ts";
export interface UnixTransportOptions {
    path: string;
    maxPendingBytes?: number;
}
/** Creates fresh Unix-domain socket transports for PiClient connection attempts in Node-compatible runtimes. */
export declare function createUnixTransportFactory(options: UnixTransportOptions): ByteTransportFactory;
//# sourceMappingURL=unix.d.ts.map
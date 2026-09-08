export interface UnixTransportAddress {
    readonly transport: "unix";
    readonly path: string;
}
export type TransportAddress = UnixTransportAddress;
export declare function parseTransportAddress(value: string, option: "--listen" | "--connect"): {
    address?: TransportAddress;
    error?: string;
};
//# sourceMappingURL=transport-address.d.ts.map
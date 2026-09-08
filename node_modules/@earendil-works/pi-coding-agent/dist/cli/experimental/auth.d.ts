export type AuthInput = {
    readonly type: "token";
    readonly token: string;
} | {
    readonly type: "file";
    readonly path: string;
};
export interface RawAuthOptions {
    readonly authToken?: string;
    readonly authTokenFile?: string;
}
export declare function parseAuthInput(options: RawAuthOptions): {
    auth?: AuthInput;
    errors: string[];
};
//# sourceMappingURL=auth.d.ts.map
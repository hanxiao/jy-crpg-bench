export function parseAuthInput(options) {
    if (options.authToken !== undefined && options.authTokenFile !== undefined) {
        return { errors: ["--auth-token and --auth-token-file are mutually exclusive"] };
    }
    if (options.authToken !== undefined) {
        return { auth: { type: "token", token: options.authToken }, errors: [] };
    }
    if (options.authTokenFile !== undefined) {
        return { auth: { type: "file", path: options.authTokenFile }, errors: [] };
    }
    return { errors: [] };
}
//# sourceMappingURL=auth.js.map
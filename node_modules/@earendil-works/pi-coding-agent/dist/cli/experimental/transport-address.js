import { posix } from "node:path";
export function parseTransportAddress(value, option) {
    let url;
    try {
        url = new URL(value);
    }
    catch {
        return { error: `Invalid ${option} address "${value}"` };
    }
    if (url.protocol !== "unix:") {
        return { error: `Unsupported ${option} transport "${url.protocol}"` };
    }
    if (url.hostname || url.port || url.username || url.password) {
        return { error: "Unix transport address must not include an authority" };
    }
    if (!value.startsWith("unix:///") ||
        value.startsWith("unix:////") ||
        value.includes("?") ||
        value.includes("#") ||
        url.href !== value) {
        return { error: `Invalid ${option} address "${value}"` };
    }
    let path;
    try {
        path = decodeURIComponent(url.pathname);
    }
    catch {
        return { error: `Invalid ${option} address "${value}"` };
    }
    if (path.includes("\0")) {
        return { error: `Invalid ${option} address "${value}"` };
    }
    if (!posix.isAbsolute(path)) {
        return { error: "Unix transport address requires an absolute path" };
    }
    return { address: { transport: "unix", path } };
}
//# sourceMappingURL=transport-address.js.map
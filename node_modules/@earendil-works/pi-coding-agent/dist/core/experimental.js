const PREFER_STRICT_TOOL_SAMPLING = { type: "json_schema", strict: "prefer" };
export function areExperimentalFeaturesEnabled() {
    return process.env.PI_EXPERIMENTAL === "1";
}
export function getExperimentalToolSampling() {
    return areExperimentalFeaturesEnabled() ? PREFER_STRICT_TOOL_SAMPLING : undefined;
}
//# sourceMappingURL=experimental.js.map
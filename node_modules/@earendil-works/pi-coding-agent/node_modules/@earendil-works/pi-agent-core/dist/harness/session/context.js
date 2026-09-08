import { createBranchSummaryMessage, createCompactionSummaryMessage } from "../messages.js";
function deriveSessionContextState(pathEntries) {
    let thinkingLevel = "off";
    let model = null;
    let activeToolNames = null;
    for (const entry of pathEntries) {
        if (entry.type === "thinking_level_change") {
            thinkingLevel = entry.thinkingLevel;
        }
        else if (entry.type === "model_change") {
            model = { provider: entry.provider, modelId: entry.modelId };
        }
        else if (entry.type === "message" && entry.message.role === "assistant") {
            model = { provider: entry.message.provider, modelId: entry.message.model };
        }
        else if (entry.type === "active_tools_change") {
            activeToolNames = [...entry.activeToolNames];
        }
    }
    return { thinkingLevel, model, activeToolNames };
}
export function defaultContextEntryTransform(pathEntries) {
    let compaction;
    let compactionIndex = -1;
    for (let index = pathEntries.length - 1; index >= 0; index--) {
        const entry = pathEntries[index];
        if (entry.type === "compaction") {
            compaction = entry;
            compactionIndex = index;
            break;
        }
    }
    return compaction === undefined ? [...pathEntries] : [compaction, ...pathEntries.slice(compactionIndex + 1)];
}
export function buildContextEntries(pathEntries, options = {}) {
    let entries = defaultContextEntryTransform(pathEntries);
    for (const transform of options.entryTransforms ?? [])
        entries = [...transform(entries)];
    return entries;
}
export function sessionEntryToContextMessages(entry, index, entries, options = {}) {
    if (entry.type === "message") {
        if (entry.message.role === "assistant" && entry.message.stopReason === "deferred")
            return [];
        return [entry.message];
    }
    if (entry.type === "compaction") {
        return [
            createCompactionSummaryMessage(entry.summary, entry.tokensBefore, entry.timestamp),
            ...entry.retainedTail,
        ];
    }
    if (entry.type === "branch_summary" && entry.summary) {
        return [createBranchSummaryMessage(entry.summary, entry.fromId, entry.timestamp)];
    }
    if (entry.type === "custom") {
        return [...(options.entryProjectors?.[entry.customType]?.(entry, index, entries) ?? [])];
    }
    return [];
}
export function buildSessionContext(pathEntries, options = {}) {
    const state = deriveSessionContextState(pathEntries);
    const contextEntries = buildContextEntries(pathEntries, options);
    const messages = contextEntries.flatMap((entry, index) => sessionEntryToContextMessages(entry, index, contextEntries, options));
    return { ...state, messages };
}
//# sourceMappingURL=context.js.map
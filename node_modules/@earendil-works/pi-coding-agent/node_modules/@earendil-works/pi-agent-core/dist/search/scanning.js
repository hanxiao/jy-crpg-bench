function defaultSearchText(_metadata, entry, label) {
    return label === undefined ? JSON.stringify(entry) : `${JSON.stringify(entry)} ${label}`;
}
async function* scanReadableEntries(readable, metadata, options, query = {}) {
    const projectText = options.projectText ?? defaultSearchText;
    const pageSize = query.limit ?? options.pageSize ?? 100;
    let afterSeq = query.afterSeq ?? 0;
    const entryTypes = query.entryTypes === undefined ? undefined : new Set(query.entryTypes);
    while (true) {
        const entries = await readable.findEntries({
            order: "oldestFirst",
            limit: pageSize,
            cursor: { afterSeq },
            type: query.entryTypes?.length === 1 ? query.entryTypes[0] : undefined,
        });
        if (entries.length === 0)
            break;
        for (const entry of entries) {
            if (entryTypes !== undefined && !entryTypes.has(entry.type))
                continue;
            const label = await readable.getLabel(entry.id);
            yield {
                entryId: entry.id,
                seq: entry.seq,
                type: entry.type,
                timestamp: entry.timestamp,
                text: projectText(metadata, entry, label),
                fields: label === undefined ? undefined : { label },
            };
        }
        afterSeq = entries[entries.length - 1]?.seq ?? afterSeq;
        if (entries.length < pageSize)
            break;
    }
}
export async function* scanningEntries(readable, options = {}) {
    yield* scanReadableEntries(readable, await readable.getMetadata(), options);
}
async function* arraySource(readables) {
    yield* readables;
}
function readablesFor(source, options) {
    return typeof source === "function" ? source(options) : arraySource(source);
}
function defaultMatch(queryText, candidate) {
    return candidate.text.toLowerCase().includes(queryText);
}
function throwIfAborted(signal) {
    if (!signal?.aborted)
        return;
    if (signal.reason instanceof Error)
        throw signal.reason;
    const error = new Error("The operation was aborted");
    error.name = "AbortError";
    throw error;
}
function createDefaultScanningHit(metadata, candidate) {
    return {
        sessionId: metadata.id,
        entryId: candidate.entryId,
        timestamp: candidate.timestamp,
        snippet: candidate.text,
    };
}
export function createScanningSessionSearch(source, options = {}) {
    const createHit = options.createHit ??
        ((metadata, candidate) => createDefaultScanningHit(metadata, candidate));
    return {
        async *search(text, searchOptions = {}) {
            const normalizedText = text.trim().toLowerCase();
            if (!normalizedText || (searchOptions.limit !== undefined && searchOptions.limit <= 0))
                return;
            if (searchOptions.entryTypes?.length === 0)
                return;
            let hitCount = 0;
            const seenSessionIds = new Set();
            const entryTypes = searchOptions.entryTypes === undefined ? undefined : new Set(searchOptions.entryTypes);
            const sourceOptions = options.sourceOptions?.(normalizedText, searchOptions);
            for await (const readable of readablesFor(source, sourceOptions)) {
                throwIfAborted(searchOptions.signal);
                const metadata = await readable.getMetadata();
                if (seenSessionIds.has(metadata.id))
                    throw new Error(`Duplicate sessionId: ${metadata.id}`);
                seenSessionIds.add(metadata.id);
                for await (const candidate of scanReadableEntries(readable, metadata, options, {
                    entryTypes: searchOptions.entryTypes,
                })) {
                    throwIfAborted(searchOptions.signal);
                    if (entryTypes !== undefined && !entryTypes.has(candidate.type))
                        continue;
                    const matches = options.match?.(normalizedText, candidate, metadata) ?? defaultMatch(normalizedText, candidate);
                    if (!matches)
                        continue;
                    yield createHit(metadata, candidate);
                    hitCount += 1;
                    if (searchOptions.limit !== undefined && hitCount >= searchOptions.limit)
                        return;
                }
            }
        },
    };
}
//# sourceMappingURL=scanning.js.map
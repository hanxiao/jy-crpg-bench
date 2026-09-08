import { SessionError, } from "./types.js";
function invalidMutation(message) {
    throw new SessionError("invalid_entry", `Invalid session mutation: ${message}`);
}
function assertValidLimit(limit) {
    if (limit !== undefined && (!Number.isInteger(limit) || limit <= 0)) {
        throw new SessionError("invalid_query", "limit must be a positive integer");
    }
}
function assertValidCursor(afterSeq) {
    if (afterSeq !== undefined && (!Number.isInteger(afterSeq) || afterSeq < 0)) {
        throw new SessionError("invalid_query", "cursor sequence must be a non-negative integer");
    }
}
function* ordered(items, order) {
    if (order === "oldestFirst") {
        yield* items;
        return;
    }
    for (let index = items.length - 1; index >= 0; index--)
        yield items[index];
}
export class SessionState {
    sequence = 0;
    usedIds = new Set();
    entries = [];
    entriesById = new Map();
    records = [];
    openOperationsByLane = new Map();
    lanes = new Map([["main", null]]);
    log = [];
    stats = {
        messageCount: 0,
        cachedTokens: 0,
        uncachedTokens: 0,
        totalTokens: 0,
        costTotal: 0,
    };
    name;
    labels = new Map();
    get nextSequence() {
        return this.sequence + 1;
    }
    getLanes() {
        return [...this.lanes].map(([lane, leafId]) => ({ lane, leafId }));
    }
    requireLane(lane) {
        const leafId = this.lanes.get(lane);
        if (leafId === undefined)
            throw new SessionError("invalid_lane", `Lane not found: ${lane}`);
        return leafId;
    }
    validateNewLane(lane) {
        if (this.lanes.has(lane))
            throw new SessionError("already_exists", `Lane already exists: ${lane}`);
    }
    validateTarget(targetId) {
        if (targetId !== null && !this.entriesById.has(targetId)) {
            throw new SessionError("not_found", `Entry not found: ${targetId}`);
        }
    }
    validateUnusedId(id) {
        if (this.usedIds.has(id))
            throw new SessionError("already_exists", `Session id already exists: ${id}`);
    }
    applyMutation(mutation, invalid = invalidMutation) {
        const seq = mutation.kind === "entry"
            ? mutation.entry.seq
            : mutation.kind === "record"
                ? mutation.record.seq
                : mutation.seq;
        if (seq !== this.sequence + 1)
            invalid(`has non-consecutive seq ${seq}`);
        switch (mutation.kind) {
            case "entry": {
                if (this.usedIds.has(mutation.entry.id))
                    invalid(`contains duplicate id ${mutation.entry.id}`);
                if (mutation.lane !== undefined) {
                    const leafId = this.lanes.get(mutation.lane);
                    if (leafId === undefined)
                        invalid(`references missing lane ${mutation.lane}`);
                    if (mutation.entry.parentId !== leafId)
                        invalid("does not chain to the lane leaf");
                }
                if (mutation.entry.parentId !== null && !this.entriesById.has(mutation.entry.parentId)) {
                    invalid(`references missing parent ${mutation.entry.parentId}`);
                }
                this.sequence = seq;
                this.usedIds.add(mutation.entry.id);
                this.entries.push(mutation.entry);
                this.entriesById.set(mutation.entry.id, mutation.entry);
                if (mutation.lane !== undefined)
                    this.lanes.set(mutation.lane, mutation.entry.id);
                this.log.push({ kind: "entry", seq, entry: mutation.entry });
                if (mutation.entry.type === "message")
                    this.stats.messageCount += 1;
                break;
            }
            case "record": {
                if (!this.lanes.has(mutation.record.lane))
                    invalid(`references missing lane ${mutation.record.lane}`);
                if (this.usedIds.has(mutation.record.id))
                    invalid(`contains duplicate id ${mutation.record.id}`);
                this.sequence = seq;
                this.usedIds.add(mutation.record.id);
                this.records.push(mutation.record);
                if (mutation.record.type === "operation_started") {
                    let openOperations = this.openOperationsByLane.get(mutation.record.lane);
                    if (!openOperations) {
                        openOperations = new Map();
                        this.openOperationsByLane.set(mutation.record.lane, openOperations);
                    }
                    openOperations.set(mutation.record.id, mutation.record);
                }
                else if (mutation.record.type === "operation_finished") {
                    this.openOperationsByLane.get(mutation.record.lane)?.delete(mutation.record.runId);
                }
                this.log.push({ kind: "record", seq, record: mutation.record });
                if (mutation.record.type === "usage") {
                    this.stats.cachedTokens += mutation.record.usage.cacheRead;
                    this.stats.uncachedTokens += mutation.record.usage.input + mutation.record.usage.cacheWrite;
                    this.stats.totalTokens += mutation.record.usage.totalTokens;
                    this.stats.costTotal += mutation.record.usage.cost.total;
                }
                break;
            }
            case "lane":
                if (mutation.leafId !== null && !this.entriesById.has(mutation.leafId)) {
                    invalid(`references missing lane target ${mutation.leafId}`);
                }
                this.sequence = seq;
                this.lanes.set(mutation.lane, mutation.leafId);
                this.log.push({ kind: "lane", seq, lane: mutation.lane, leafId: mutation.leafId });
                break;
            case "fact":
                if (mutation.fact === "label" && !this.entriesById.has(mutation.targetId)) {
                    invalid(`references missing label target ${mutation.targetId}`);
                }
                this.sequence = seq;
                if (mutation.fact === "name") {
                    this.name = mutation.name;
                    this.log.push({ kind: "fact", seq, fact: "name", name: mutation.name });
                }
                else {
                    if (mutation.label === undefined)
                        this.labels.delete(mutation.targetId);
                    else
                        this.labels.set(mutation.targetId, mutation.label);
                    this.log.push({
                        kind: "fact",
                        seq,
                        fact: "label",
                        targetId: mutation.targetId,
                        label: mutation.label,
                    });
                }
                break;
        }
    }
    getEntry(id) {
        return this.entriesById.get(id);
    }
    findEntries(query = {}) {
        assertValidLimit(query.limit);
        assertValidCursor(query.cursor?.afterSeq);
        const results = [];
        for (const entry of ordered(this.entries, query.order)) {
            if (!this.matchesEntryQuery(entry, query))
                continue;
            results.push(entry);
            if (results.length === query.limit)
                break;
        }
        return results;
    }
    findEntriesOnBranch(query) {
        assertValidLimit(query.limit);
        assertValidCursor(query.cursor?.afterSeq);
        const results = [];
        if (query.order === "oldestFirst") {
            for (const entry of [...this.walkToRoot(query.start)].reverse()) {
                const reachedBound = entry.id === query.stopAtId || entry.type === query.stopAtType;
                if (this.matchesEntryQuery(entry, query))
                    results.push(entry);
                if (reachedBound || results.length === query.limit)
                    break;
            }
        }
        else {
            for (const entry of this.walkToRoot(query.start, query)) {
                if (this.matchesEntryQuery(entry, query))
                    results.push(entry);
                if (results.length === query.limit)
                    break;
            }
        }
        return results;
    }
    findRecords(query = {}) {
        assertValidLimit(query.limit);
        assertValidCursor(query.afterSeq);
        const results = [];
        for (const record of ordered(this.records, query.order)) {
            if (!this.matchesRecordQuery(record, query))
                continue;
            results.push(record);
            if (results.length === query.limit)
                break;
        }
        return results;
    }
    findOpenOperations(lane, options) {
        assertValidLimit(options?.limit);
        const openOperationsById = this.openOperationsByLane.get(lane);
        const openOperations = openOperationsById ? [...openOperationsById.values()].reverse() : [];
        return options?.limit === undefined ? openOperations : openOperations.slice(0, options.limit);
    }
    getLog(options = {}) {
        assertValidLimit(options.limit);
        assertValidCursor(options.afterSeq);
        const results = [];
        for (const item of this.log) {
            if (options.afterSeq !== undefined && item.seq <= options.afterSeq)
                continue;
            results.push(item);
            if (results.length === options.limit)
                break;
        }
        return results;
    }
    getName() {
        return this.name;
    }
    getLabel(id) {
        return this.labels.get(id);
    }
    getStats() {
        return this.stats;
    }
    createForkMutations(options) {
        let copiedEntries;
        let forkLanes;
        if (options.scope === "tree") {
            copiedEntries = this.findEntries({ order: "oldestFirst" });
            forkLanes = this.getLanes();
        }
        else {
            const selectedEntryId = options.entryId ?? this.requireLane("main");
            let targetId = null;
            if (selectedEntryId !== null) {
                const entry = this.getEntry(selectedEntryId);
                if (!entry || entry.type !== "message") {
                    throw new SessionError("invalid_fork_target", `Fork target is not a message entry: ${selectedEntryId}`);
                }
                const position = options.position ?? (options.entryId === undefined ? "at" : "before");
                targetId = position === "at" ? entry.id : entry.parentId;
            }
            copiedEntries = targetId === null ? [] : this.findEntriesOnBranch({ start: targetId, order: "oldestFirst" });
            forkLanes = [{ lane: "main", leafId: targetId }];
        }
        const mutations = [];
        let sequence = 1;
        for (const sourceEntry of copiedEntries) {
            mutations.push({ kind: "entry", entry: { ...structuredClone(sourceEntry), seq: sequence++ } });
        }
        for (const pointer of forkLanes) {
            mutations.push({ kind: "lane", seq: sequence++, lane: pointer.lane, leafId: pointer.leafId });
        }
        if (this.name !== undefined) {
            mutations.push({ kind: "fact", seq: sequence++, fact: "name", name: this.name });
        }
        for (const entry of copiedEntries) {
            const label = this.labels.get(entry.id);
            if (label !== undefined) {
                mutations.push({ kind: "fact", seq: sequence++, fact: "label", targetId: entry.id, label });
            }
        }
        return mutations;
    }
    *walkToRoot(start, bounds) {
        if (start === null)
            return;
        const visited = new Set();
        let current = this.entriesById.get(start);
        if (!current)
            throw new SessionError("not_found", `Entry not found: ${start}`);
        while (current) {
            if (visited.has(current.id)) {
                throw new SessionError("invalid_entry", `Session branch contains a cycle at ${current.id}`);
            }
            visited.add(current.id);
            yield current;
            if (current.id === bounds?.stopAtId || current.type === bounds?.stopAtType || current.parentId === null)
                break;
            const parentId = current.parentId;
            current = this.entriesById.get(parentId);
            if (!current)
                throw new SessionError("invalid_entry", `Entry not found: ${parentId}`);
        }
    }
    matchesEntryQuery(entry, query) {
        return ((query.type === undefined || entry.type === query.type) &&
            (query.customType === undefined || (entry.type === "custom" && entry.customType === query.customType)) &&
            (query.cursor === undefined ||
                (query.order === "oldestFirst" ? entry.seq > query.cursor.afterSeq : entry.seq < query.cursor.afterSeq)));
    }
    matchesRecordQuery(record, query) {
        return ((query.lane === undefined || record.lane === query.lane) &&
            (query.type === undefined || record.type === query.type) &&
            (query.runId === undefined ||
                (record.type === "operation_started"
                    ? record.id === query.runId
                    : "runId" in record && record.runId === query.runId)) &&
            (query.operationKind === undefined ||
                (record.type === "operation_started" && record.intent.kind === query.operationKind)) &&
            (query.afterSeq === undefined || record.seq > query.afterSeq));
    }
}
//# sourceMappingURL=state.js.map
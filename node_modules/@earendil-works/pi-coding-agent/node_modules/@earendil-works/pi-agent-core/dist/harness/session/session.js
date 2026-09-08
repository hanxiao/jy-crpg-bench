import { uuidv7 } from "@earendil-works/pi-ai";
import { SessionError } from "./types.js";
function invalidPayload(reason) {
    throw new SessionError("invalid_payload", `Durable payload ${reason}`);
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
export function assertJsonSerializable(value) {
    const active = new WeakSet();
    const stack = [{ value }];
    while (stack.length > 0) {
        const frame = stack.pop();
        if ("exit" in frame) {
            active.delete(frame.exit);
            continue;
        }
        const candidate = frame.value;
        if (candidate === null || typeof candidate === "string" || typeof candidate === "boolean") {
            continue;
        }
        if (typeof candidate === "number") {
            if (!Number.isFinite(candidate))
                invalidPayload("contains a non-finite number");
            continue;
        }
        if (typeof candidate !== "object")
            invalidPayload(`contains ${typeof candidate}`);
        if (active.has(candidate))
            invalidPayload("contains a cycle");
        active.add(candidate);
        stack.push({ exit: candidate });
        if (Array.isArray(candidate)) {
            if (Object.getPrototypeOf(candidate) !== Array.prototype) {
                invalidPayload("contains a non-standard array");
            }
            if (Object.getOwnPropertySymbols(candidate).length > 0 ||
                Object.getOwnPropertyNames(candidate).length !== candidate.length + 1) {
                invalidPayload("contains an array with unsupported properties");
            }
            for (let index = candidate.length - 1; index >= 0; index--) {
                if (!Object.hasOwn(candidate, index))
                    invalidPayload("contains a sparse array");
                const descriptor = Object.getOwnPropertyDescriptor(candidate, index);
                if (!("value" in descriptor))
                    invalidPayload("contains an array accessor");
                stack.push({ value: descriptor.value });
            }
            continue;
        }
        const prototype = Object.getPrototypeOf(candidate);
        if (prototype !== Object.prototype && prototype !== null) {
            invalidPayload("contains a non-plain object");
        }
        if (Object.getOwnPropertySymbols(candidate).length > 0) {
            invalidPayload("contains a symbol-keyed property");
        }
        const keys = Object.keys(candidate);
        if (Object.getOwnPropertyNames(candidate).length !== keys.length) {
            invalidPayload("contains a non-enumerable property");
        }
        for (let index = keys.length - 1; index >= 0; index--) {
            const descriptor = Object.getOwnPropertyDescriptor(candidate, keys[index]);
            if (!("value" in descriptor))
                invalidPayload("contains an accessor");
            stack.push({ value: descriptor.value });
        }
    }
}
export class Session {
    storage;
    idGenerator;
    constructor(storage, options = {}) {
        this.storage = storage;
        this.idGenerator = options.idGenerator ?? { next: () => uuidv7() };
    }
    async getMetadata() {
        return this.storage.getMetadata();
    }
    view(lane) {
        if (lane === "main")
            return this;
        return {
            getLeafId: () => this.getLeafIdForLane(lane),
            getEntry: (id) => this.getEntry(id),
            getStats: () => this.getStats(),
            getName: () => this.getName(),
            setName: (name) => this.setName(name),
            getLabel: (targetId) => this.getLabel(targetId),
            setLabel: (targetId, label) => this.setLabel(targetId, label),
            findEntries: (query) => this.queryEntries(query),
            findEntry: async (query = {}) => (await this.queryEntries(query, 1))[0],
            findEntriesOnBranch: (query) => this.queryBranchEntries(lane, query),
            findEntryOnBranch: async (query = {}) => (await this.queryBranchEntries(lane, query, 1))[0],
            appendMessage: (message) => this.appendMessageToLane(lane, message),
            appendCustomEntry: (customType, data) => this.appendCustomEntryToLane(lane, customType, data),
        };
    }
    async getLeafId() {
        return this.getLeafIdForLane("main");
    }
    async getEntry(id) {
        return this.storage.getEntry(id);
    }
    async getStats() {
        return this.storage.getStats();
    }
    async getName() {
        return this.storage.getName();
    }
    async setName(name) {
        await this.storage.setName(name);
    }
    async getLabel(targetId) {
        return this.storage.getLabel(targetId);
    }
    async setLabel(targetId, label) {
        await this.storage.setLabel(targetId, label);
    }
    async findEntries(query) {
        return this.queryEntries(query);
    }
    async findEntry(query = {}) {
        return (await this.queryEntries(query, 1))[0];
    }
    async findEntriesOnBranch(query) {
        return this.queryBranchEntries("main", query);
    }
    async findEntryOnBranch(query = {}) {
        return (await this.queryBranchEntries("main", query, 1))[0];
    }
    async appendMessage(message) {
        return this.appendMessageToLane("main", message);
    }
    async appendCustomEntry(customType, data) {
        return this.appendCustomEntryToLane("main", customType, data);
    }
    async getLanes() {
        return this.storage.getLanes();
    }
    async createLane(lane, at) {
        await this.storage.createLane(lane, at);
    }
    async moveLane(lane, to) {
        await this.storage.moveLane(lane, to);
    }
    async appendEntry(entry, lane) {
        return this.commitEntry(entry, lane);
    }
    async appendRecord(record) {
        return this.commitRecord(record);
    }
    async findRecords(query) {
        return this.queryRecords(query);
    }
    async findOpenOperations(lane, options) {
        assertValidLimit(options?.limit);
        return this.storage.findOpenOperations(lane, options);
    }
    async getLog(options) {
        return this.queryLog(options);
    }
    /** Returns the lane's current leaf, or null when empty. Throws when the lane does not exist. */
    async getLeafIdForLane(lane) {
        const pointer = (await this.getLanes()).find((candidate) => candidate.lane === lane);
        if (!pointer)
            throw new SessionError("invalid_lane", `Lane not found: ${lane}`);
        return pointer.leafId;
    }
    async queryEntries(query = {}, resultLimit = query.limit) {
        assertValidLimit(query.limit);
        assertValidCursor(query.cursor?.afterSeq);
        return this.storage.findEntries(resultLimit === query.limit ? query : { ...query, limit: resultLimit });
    }
    /**
     * Queries from `query.start` toward the root, defaulting to the lane's current leaf.
     * `resultLimit` lets single-entry queries cap results without changing the caller's query.
     */
    async queryBranchEntries(defaultLane, query = {}, resultLimit = query.limit) {
        assertValidLimit(query.limit);
        assertValidCursor(query.cursor?.afterSeq);
        const start = query.start ?? (await this.getLeafIdForLane(defaultLane));
        if (start === null)
            return [];
        const storageQuery = resultLimit === query.limit ? query : { ...query, limit: resultLimit };
        return this.storage.findEntriesOnBranch({ ...storageQuery, start });
    }
    async queryRecords(query = {}) {
        assertValidLimit(query.limit);
        assertValidCursor(query.afterSeq);
        if (query.operationKind !== undefined && query.type !== "operation_started") {
            throw new SessionError("invalid_query", 'operationKind requires type "operation_started"');
        }
        return this.storage.findRecords(query);
    }
    async queryLog(options = {}) {
        assertValidLimit(options.limit);
        assertValidCursor(options.afterSeq);
        return this.storage.getLog(options);
    }
    async appendMessageToLane(lane, message) {
        const entry = await this.commitEntry({ type: "message", id: this.idGenerator.next(), message }, lane);
        return entry.id;
    }
    async appendCustomEntryToLane(lane, customType, data) {
        const entry = await this.commitEntry(data === undefined
            ? { type: "custom", id: this.idGenerator.next(), customType }
            : { type: "custom", id: this.idGenerator.next(), customType, data }, lane);
        return entry.id;
    }
    async commitEntry(entry, lane) {
        assertJsonSerializable(entry);
        return this.storage.appendEntry(entry, lane);
    }
    async commitRecord(record) {
        assertJsonSerializable(record);
        return this.storage.appendRecord(record);
    }
}
//# sourceMappingURL=session.js.map
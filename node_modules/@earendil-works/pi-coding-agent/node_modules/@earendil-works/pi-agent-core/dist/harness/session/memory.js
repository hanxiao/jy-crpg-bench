import { uuidv7 } from "@earendil-works/pi-ai";
import { Session } from "./session.js";
import { SessionState } from "./state.js";
import { SessionError, } from "./types.js";
export class InMemorySessionStorage {
    metadata;
    state = new SessionState();
    constructor(metadata) {
        this.metadata = structuredClone(metadata);
    }
    fork(metadata, options) {
        const storage = new InMemorySessionStorage(metadata);
        for (const mutation of this.state.createForkMutations(options))
            storage.state.applyMutation(mutation);
        return storage;
    }
    async getMetadata() {
        return structuredClone(this.metadata);
    }
    async getLanes() {
        return this.state.getLanes();
    }
    async createLane(lane, at) {
        this.state.validateNewLane(lane);
        this.state.validateTarget(at);
        this.state.applyMutation({ kind: "lane", seq: this.state.nextSequence, lane, leafId: at });
    }
    async moveLane(lane, to) {
        this.state.requireLane(lane);
        this.state.validateTarget(to);
        this.state.applyMutation({ kind: "lane", seq: this.state.nextSequence, lane, leafId: to });
    }
    async appendEntry(newEntry, lane) {
        const parentId = this.state.requireLane(lane);
        this.state.validateUnusedId(newEntry.id);
        const entry = {
            ...structuredClone(newEntry),
            parentId,
            seq: this.state.nextSequence,
            timestamp: Date.now(),
        };
        this.state.applyMutation({ kind: "entry", lane, entry });
        return structuredClone(entry);
    }
    async appendRecord(newRecord) {
        this.state.requireLane(newRecord.lane);
        this.state.validateUnusedId(newRecord.id);
        const currentOpenOperationId = this.state.findOpenOperations(newRecord.lane, { limit: 1 })[0]?.id;
        if (newRecord.type === "operation_started" && currentOpenOperationId !== undefined) {
            throw new SessionError("storage", `Lane ${newRecord.lane} already has an open operation ${currentOpenOperationId}`);
        }
        const record = {
            ...structuredClone(newRecord),
            seq: this.state.nextSequence,
            timestamp: Date.now(),
        };
        this.state.applyMutation({ kind: "record", record });
        return structuredClone(record);
    }
    async getEntry(id) {
        const entry = this.state.getEntry(id);
        return entry === undefined ? undefined : structuredClone(entry);
    }
    async findEntries(query = {}) {
        return structuredClone(this.state.findEntries(query));
    }
    async findEntriesOnBranch(query) {
        return structuredClone(this.state.findEntriesOnBranch(query));
    }
    async findRecords(query = {}) {
        return structuredClone(this.state.findRecords(query));
    }
    async findOpenOperations(lane, options) {
        return structuredClone(this.state.findOpenOperations(lane, options));
    }
    async getLog(options = {}) {
        return structuredClone(this.state.getLog(options));
    }
    async getName() {
        return this.state.getName();
    }
    async setName(name) {
        this.state.applyMutation({ kind: "fact", seq: this.state.nextSequence, fact: "name", name });
    }
    async getLabel(id) {
        return this.state.getLabel(id);
    }
    async setLabel(id, label) {
        this.state.validateTarget(id);
        this.state.applyMutation({
            kind: "fact",
            seq: this.state.nextSequence,
            fact: "label",
            targetId: id,
            label,
        });
    }
    async getStats() {
        return structuredClone(this.state.getStats());
    }
}
export class InMemorySessionRepo {
    sessions = new Map();
    async create(options = {}) {
        const id = options.id ?? uuidv7();
        if (this.sessions.has(id))
            throw new SessionError("already_exists", `Session already exists: ${id}`);
        const storage = new InMemorySessionStorage({
            id,
            createdAt: Date.now(),
            parentSessionId: options.parentSessionId,
        });
        this.sessions.set(id, storage);
        return new Session(storage);
    }
    async open(metadata) {
        return new Session(this.requireStorage(metadata.id));
    }
    async list() {
        return Promise.all([...this.sessions.values()].map((storage) => storage.getMetadata()));
    }
    async delete(metadata) {
        this.sessions.delete(metadata.id);
    }
    async fork(source, options = {}) {
        const sourceStorage = this.requireStorage(source.id);
        const id = options.id ?? uuidv7();
        if (this.sessions.has(id))
            throw new SessionError("already_exists", `Session already exists: ${id}`);
        const storage = sourceStorage.fork({ id, createdAt: Date.now(), parentSessionId: options.parentSessionId ?? source.id }, options);
        this.sessions.set(id, storage);
        return new Session(storage);
    }
    requireStorage(id) {
        const storage = this.sessions.get(id);
        if (!storage)
            throw new SessionError("not_found", `Session not found: ${id}`);
        return storage;
    }
}
//# sourceMappingURL=memory.js.map
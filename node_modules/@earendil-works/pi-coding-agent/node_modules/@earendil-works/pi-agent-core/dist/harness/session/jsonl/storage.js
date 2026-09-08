import { SessionState } from "../state.js";
import { SessionError, } from "../types.js";
import { encodeHeader, encodeMutation, metadataFromHeader, parseHeader, parseMutation } from "./codec.js";
import { fileResult, invalidFile, JsonlDecodeError } from "./errors.js";
/**
 * Build a complete sibling temporary file, then atomically rename it over the destination.
 * The populate callback must create or overwrite `tempPath` with the complete file. The
 * destination is untouched until the rename commits, so a process crash while populating
 * can leave only the ignored `.tmp` file behind.
 *
 * Rejects when population or rename fails. On rejection, temporary-file removal is
 * best-effort and the original error is preserved. Callers must serialize publications to
 * the same destination because they share its deterministic `.tmp` path.
 */
async function publishFileAtomically(fs, destinationPath, populate) {
    const tempPath = `${destinationPath}.tmp`;
    try {
        await populate(tempPath);
        fileResult(await fs.renameFile(tempPath, destinationPath), `Failed to publish staged file ${destinationPath}`);
    }
    catch (error) {
        await fs.remove(tempPath, { force: true });
        throw error;
    }
}
export class JsonlSessionStorage {
    fs;
    metadata;
    state = new SessionState();
    tail = Promise.resolve();
    constructor(fs, metadata) {
        this.fs = fs;
        this.metadata = structuredClone(metadata);
    }
    static async create(fs, path, header) {
        fileResult(await fs.writeFile(path, encodeHeader(header)), `Failed to initialize session ${path}`);
        const fileInfo = fileResult(await fs.fileInfo(path), `Failed to read session metadata ${path}`);
        return new JsonlSessionStorage(fs, metadataFromHeader(header, path, fileInfo.mtimeMs));
    }
    static async load(fs, path) {
        const content = fileResult(await fs.readTextFile(path), `Failed to read session ${path}`);
        const physicalLines = content.split("\n");
        if (physicalLines.at(-1) === "")
            physicalLines.pop();
        if (physicalLines.length === 0 || !physicalLines[0]) {
            throw invalidFile(path, 1, new JsonlDecodeError("schema", "is missing a header"));
        }
        const headerResult = parseHeader(physicalLines[0]);
        if (!headerResult.ok)
            throw invalidFile(path, 1, headerResult.error);
        const fileInfo = fileResult(await fs.fileInfo(path), `Failed to read session metadata ${path}`);
        const storage = new JsonlSessionStorage(fs, metadataFromHeader(headerResult.value, path, fileInfo.mtimeMs));
        for (let index = 1; index < physicalLines.length; index++) {
            const line = physicalLines[index];
            const mutationResult = parseMutation(line);
            if (!mutationResult.ok) {
                const isTornTail = index === physicalLines.length - 1 && mutationResult.error.kind === "syntax";
                if (isTornTail) {
                    // Drop the unacknowledged partial append by atomically publishing the valid prefix.
                    const validPrefix = `${physicalLines.slice(0, index).join("\n")}\n`;
                    await publishFileAtomically(fs, path, async (tempPath) => {
                        fileResult(await fs.writeFile(tempPath, validPrefix), `Failed to stage torn-tail repair ${path}`);
                    });
                    return storage;
                }
                throw invalidFile(path, index + 1, mutationResult.error);
            }
            try {
                storage.applyMutation(mutationResult.value);
            }
            catch (error) {
                if (error instanceof SessionError && error.code === "invalid_entry") {
                    throw invalidFile(path, index + 1, error);
                }
                throw error;
            }
        }
        if (!content.endsWith("\n")) {
            fileResult(await fs.appendFile(path, "\n"), `Failed to repair unterminated session tail ${path}`);
        }
        return storage;
    }
    async fork(path, header, options) {
        const mutations = this.state.createForkMutations(options);
        await publishFileAtomically(this.fs, path, async (tempPath) => {
            const targetStorage = await JsonlSessionStorage.create(this.fs, tempPath, header);
            for (const mutation of mutations) {
                await targetStorage.appendMutation(mutation);
                targetStorage.applyMutation(mutation);
            }
        });
        return JsonlSessionStorage.load(this.fs, path);
    }
    async drain() {
        await this.tail;
    }
    async getMetadata() {
        return structuredClone(this.metadata);
    }
    async getLanes() {
        return this.state.getLanes();
    }
    createLane(lane, at) {
        return this.enqueue(async () => {
            this.state.validateNewLane(lane);
            this.state.validateTarget(at);
            const mutation = { kind: "lane", seq: this.state.nextSequence, lane, leafId: at };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
        });
    }
    moveLane(lane, to) {
        return this.enqueue(async () => {
            this.state.requireLane(lane);
            this.state.validateTarget(to);
            const mutation = { kind: "lane", seq: this.state.nextSequence, lane, leafId: to };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
        });
    }
    appendEntry(newEntry, lane) {
        return this.enqueue(async () => {
            const parentId = this.state.requireLane(lane);
            this.state.validateUnusedId(newEntry.id);
            const entry = {
                ...structuredClone(newEntry),
                parentId,
                seq: this.state.nextSequence,
                timestamp: Date.now(),
            };
            const mutation = { kind: "entry", lane, entry };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
            return structuredClone(entry);
        });
    }
    appendRecord(newRecord) {
        return this.enqueue(async () => {
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
            const mutation = { kind: "record", record };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
            return structuredClone(record);
        });
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
    setName(name) {
        return this.enqueue(async () => {
            const mutation = { kind: "fact", seq: this.state.nextSequence, fact: "name", name };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
        });
    }
    async getLabel(id) {
        return this.state.getLabel(id);
    }
    setLabel(id, label) {
        return this.enqueue(async () => {
            this.state.validateTarget(id);
            const mutation = {
                kind: "fact",
                seq: this.state.nextSequence,
                fact: "label",
                targetId: id,
                label,
            };
            await this.appendMutation(mutation);
            this.applyMutation(mutation);
        });
    }
    async getStats() {
        return structuredClone(this.state.getStats());
    }
    enqueue(operation) {
        const result = this.tail.then(operation);
        this.tail = result.then(() => undefined, () => undefined);
        return result;
    }
    async appendMutation(mutation) {
        fileResult(await this.fs.appendFile(this.metadata.path, encodeMutation(mutation)), `Failed to append session ${this.metadata.path}`);
    }
    applyMutation(mutation) {
        this.state.applyMutation(mutation);
    }
}
//# sourceMappingURL=storage.js.map
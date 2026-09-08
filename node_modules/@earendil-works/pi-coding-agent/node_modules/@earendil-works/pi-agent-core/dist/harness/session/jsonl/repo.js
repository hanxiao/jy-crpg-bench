import { uuidv7 } from "@earendil-works/pi-ai";
import { assertJsonSerializable, Session } from "../session.js";
import { SessionError } from "../types.js";
import { metadataFromHeader, parseHeader } from "./codec.js";
import { fileResult } from "./errors.js";
import { JsonlSessionStorage } from "./storage.js";
const SESSION_ID_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$/;
function validateSessionId(id) {
    if (!SESSION_ID_PATTERN.test(id)) {
        throw new SessionError("invalid_payload", "Session id must be non-empty, contain only alphanumeric characters, '-', '_', and '.', and start and end with an alphanumeric character");
    }
}
function jsonlSessionDirectoryName(cwd) {
    return `--${cwd.replace(/^[/\\]/, "").replace(/[/\\:]/g, "-")}--`;
}
async function jsonlSessionsRoot(options) {
    return fileResult(await options.fs.absolutePath(options.sessionsRoot), `Failed to resolve sessions root ${options.sessionsRoot}`);
}
async function jsonlSessionDirectory(fs, sessionsRoot, cwd) {
    return fileResult(await fs.joinPath([sessionsRoot, jsonlSessionDirectoryName(cwd)]), `Failed to resolve sessions directory for ${cwd}`);
}
async function jsonlSessionDirectories(options, cwd) {
    const sessionsRoot = await jsonlSessionsRoot(options);
    if (cwd !== undefined) {
        const resolvedCwd = fileResult(await options.fs.absolutePath(cwd), `Failed to resolve session cwd ${cwd}`);
        const directory = await jsonlSessionDirectory(options.fs, sessionsRoot, resolvedCwd);
        return fileResult(await options.fs.exists(directory), `Failed to check sessions directory ${directory}`)
            ? [directory]
            : [];
    }
    if (!fileResult(await options.fs.exists(sessionsRoot), `Failed to check sessions directory ${sessionsRoot}`))
        return [];
    return fileResult(await options.fs.listDir(sessionsRoot), `Failed to list sessions directory ${sessionsRoot}`)
        .filter((entry) => entry.kind === "directory" || entry.kind === "symlink")
        .map((entry) => entry.path);
}
export async function listJsonlSessionMetadata(options, query = {}) {
    const metadata = [];
    for (const directory of await jsonlSessionDirectories(options, query.cwd)) {
        const files = fileResult(await options.fs.listDir(directory), `Failed to list sessions directory ${directory}`).filter((entry) => entry.kind !== "directory" && entry.name.endsWith(".jsonl"));
        for (const file of files) {
            const [firstLine] = fileResult(await options.fs.readTextLines(file.path, { maxLines: 1 }), `Failed to read session header ${file.path}`);
            if (!firstLine)
                continue;
            const headerResult = parseHeader(firstLine);
            if (!headerResult.ok)
                continue;
            metadata.push(metadataFromHeader(headerResult.value, file.path, file.mtimeMs));
        }
    }
    return metadata.sort((left, right) => right.modifiedAt - left.modifiedAt);
}
export async function loadJsonlSessionStorage(options, metadata) {
    if (!fileResult(await options.fs.exists(metadata.path), `Failed to check session ${metadata.path}`)) {
        throw new SessionError("not_found", `Session not found: ${metadata.id}`);
    }
    const storage = await JsonlSessionStorage.load(options.fs, metadata.path);
    const loadedMetadata = await storage.getMetadata();
    if (loadedMetadata.id !== metadata.id) {
        throw new SessionError("invalid_entry", `Session id does not match header: ${metadata.id}`);
    }
    return storage;
}
function sessionFileName(createdAt, id) {
    const timestamp = new Date(createdAt).toISOString().replace(/[:.]/g, "-");
    return `${timestamp}_${id}.jsonl`;
}
export class JsonlSessionRepo {
    fs;
    sessionsRootInput;
    activeCreateDestinations = new Set();
    rootPromise;
    constructor(options) {
        this.fs = options.fs;
        this.sessionsRootInput = options.sessionsRoot;
    }
    async create(options) {
        const destination = await this.resolveCreateDestination(options);
        return this.claimCreateDestination(destination, async () => {
            const { header, path } = await this.prepareCreate(destination, options);
            return new Session(await JsonlSessionStorage.create(this.fs, path, header));
        });
    }
    async open(metadata) {
        return new Session(await this.loadStorage(metadata));
    }
    async list(options = {}) {
        return this.listDirect(options);
    }
    async delete(metadata) {
        fileResult(await this.fs.remove(metadata.path, { force: true }), `Failed to delete session ${metadata.path}`);
    }
    async fork(source, options) {
        const sourceStorage = await this.loadStorage(source);
        const createOptions = {
            ...options,
            parentSessionId: options.parentSessionId ?? source.id,
        };
        const destination = await this.resolveCreateDestination(createOptions);
        return this.claimCreateDestination(destination, async () => {
            const { header, path } = await this.prepareCreate(destination, createOptions);
            return new Session(await sourceStorage.fork(path, header, options));
        });
    }
    async loadStorage(metadata) {
        return loadJsonlSessionStorage({ fs: this.fs, sessionsRoot: this.sessionsRootInput }, metadata);
    }
    async resolveCreateDestination(options) {
        const id = options.id ?? uuidv7();
        validateSessionId(id);
        const cwd = fileResult(await this.fs.absolutePath(options.cwd), `Failed to resolve session cwd ${options.cwd}`);
        return { id, cwd };
    }
    /**
     * Prevent same-process create/fork races for one logical destination. The durable filename includes a
     * timestamp, so the async filesystem existence check alone can let two concurrent calls both decide the
     * same {cwd, id} is free and publish duplicate sessions.
     */
    async claimCreateDestination(destination, operation) {
        const key = `${destination.cwd}\0${destination.id}`;
        if (this.activeCreateDestinations.has(key)) {
            throw new SessionError("already_exists", `Session already exists: ${destination.id}`);
        }
        this.activeCreateDestinations.add(key);
        try {
            return await operation();
        }
        finally {
            this.activeCreateDestinations.delete(key);
        }
    }
    async prepareCreate(destination, options) {
        const { id, cwd } = destination;
        if (await this.sessionIdExists(id, cwd)) {
            throw new SessionError("already_exists", `Session already exists: ${id}`);
        }
        const createdAt = Date.now();
        const sessionDirectory = await this.sessionDirectory(cwd);
        const path = fileResult(await this.fs.joinPath([sessionDirectory, sessionFileName(createdAt, id)]), `Failed to resolve path for session ${id}`);
        if (options.metadata !== undefined)
            assertJsonSerializable(options.metadata);
        const header = {
            kind: "header",
            version: 4,
            id,
            createdAt,
            cwd,
            parentSessionId: options.parentSessionId,
            metadata: options.metadata,
        };
        fileResult(await this.fs.createDir(sessionDirectory, { recursive: true }), `Failed to create sessions directory`);
        return { header, path };
    }
    async listDirect(options) {
        return listJsonlSessionMetadata({ fs: this.fs, sessionsRoot: this.sessionsRootInput }, options);
    }
    async sessionIdExists(id, cwd) {
        const suffix = `_${id}.jsonl`;
        const directory = await this.sessionDirectory(cwd);
        if (!fileResult(await this.fs.exists(directory), `Failed to check sessions directory ${directory}`))
            return false;
        const files = fileResult(await this.fs.listDir(directory), `Failed to list sessions directory ${directory}`);
        return files.some((entry) => entry.kind !== "directory" && entry.name.endsWith(suffix));
    }
    async sessionDirectory(cwd) {
        return fileResult(await this.fs.joinPath([await this.root(), jsonlSessionDirectoryName(cwd)]), `Failed to resolve sessions directory for ${cwd}`);
    }
    root() {
        this.rootPromise ??= this.fs
            .absolutePath(this.sessionsRootInput)
            .then((result) => fileResult(result, `Failed to resolve sessions root ${this.sessionsRootInput}`));
        return this.rootPromise;
    }
}
//# sourceMappingURL=repo.js.map
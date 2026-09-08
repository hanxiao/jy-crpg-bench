import { type BranchBounds, type Entry, type EntryQuery, type ForkOptions, type LanePointer, type LaneRecord, type LogItem, type LogOptions, type NewRecord, type OperationStartedRecord, type ProvisionedEntry, type RecordQuery, type SessionStats, type SessionStorage } from "../types.ts";
import type { JsonlSessionMetadata, JsonlSessionRepoFileSystem, JsonlV4Header } from "./types.ts";
export declare class JsonlSessionStorage implements SessionStorage<JsonlSessionMetadata> {
    private readonly fs;
    private readonly metadata;
    private readonly state;
    private tail;
    constructor(fs: JsonlSessionRepoFileSystem, metadata: JsonlSessionMetadata);
    static create(fs: JsonlSessionRepoFileSystem, path: string, header: JsonlV4Header): Promise<JsonlSessionStorage>;
    static load(fs: JsonlSessionRepoFileSystem, path: string): Promise<JsonlSessionStorage>;
    fork(path: string, header: JsonlV4Header, options: ForkOptions): Promise<JsonlSessionStorage>;
    drain(): Promise<void>;
    getMetadata(): Promise<JsonlSessionMetadata>;
    getLanes(): Promise<LanePointer[]>;
    createLane(lane: string, at: string | null): Promise<void>;
    moveLane(lane: string, to: string | null): Promise<void>;
    appendEntry<TEntry extends Entry>(newEntry: ProvisionedEntry<TEntry>, lane: string): Promise<TEntry>;
    appendRecord<TRecord extends LaneRecord>(newRecord: NewRecord<TRecord>): Promise<TRecord>;
    getEntry(id: string): Promise<Entry | undefined>;
    findEntries(query?: EntryQuery): Promise<Entry[]>;
    findEntriesOnBranch(query: EntryQuery & BranchBounds & {
        start: string;
    }): Promise<Entry[]>;
    findRecords<K extends LaneRecord["type"]>(query: RecordQuery & {
        type: K;
    }): Promise<Extract<LaneRecord, {
        type: K;
    }>[]>;
    findRecords(query?: RecordQuery): Promise<LaneRecord[]>;
    findOpenOperations(lane: string, options?: {
        limit?: number;
    }): Promise<OperationStartedRecord[]>;
    getLog(options?: LogOptions): Promise<LogItem[]>;
    getName(): Promise<string | undefined>;
    setName(name: string | undefined): Promise<void>;
    getLabel(id: string): Promise<string | undefined>;
    setLabel(id: string, label: string | undefined): Promise<void>;
    getStats(): Promise<SessionStats>;
    private enqueue;
    private appendMutation;
    private applyMutation;
}
//# sourceMappingURL=storage.d.ts.map
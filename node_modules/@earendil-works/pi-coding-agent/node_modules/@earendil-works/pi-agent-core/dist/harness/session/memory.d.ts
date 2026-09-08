import { Session } from "./session.ts";
import { type BranchBounds, type Entry, type EntryQuery, type ForkOptions, type LanePointer, type LaneRecord, type LogItem, type LogOptions, type NewRecord, type OperationStartedRecord, type ProvisionedEntry, type RecordQuery, type SessionCreateOptions, type SessionMetadata, type SessionRepo, type SessionStats, type SessionStorage } from "./types.ts";
export declare class InMemorySessionStorage implements SessionStorage {
    private readonly metadata;
    private readonly state;
    constructor(metadata: SessionMetadata);
    fork(metadata: SessionMetadata, options: ForkOptions & SessionCreateOptions): InMemorySessionStorage;
    getMetadata(): Promise<SessionMetadata>;
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
}
export declare class InMemorySessionRepo implements SessionRepo {
    private readonly sessions;
    create(options?: SessionCreateOptions): Promise<Session>;
    open(metadata: SessionMetadata): Promise<Session>;
    list(): Promise<SessionMetadata[]>;
    delete(metadata: SessionMetadata): Promise<void>;
    fork(source: SessionMetadata, options?: ForkOptions & SessionCreateOptions): Promise<Session>;
    private requireStorage;
}
//# sourceMappingURL=memory.d.ts.map
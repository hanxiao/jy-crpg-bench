import type { AgentMessage } from "../../types.ts";
import type { BranchBounds, Entry, EntryQuery, IdGenerator, LanePointer, LaneRecord, LogItem, LogOptions, NewRecord, OperationStartedRecord, ProvisionedEntry, RecordBase, RecordQuery, SessionMetadata, SessionStats, SessionStorage, SessionTree } from "./types.ts";
export declare function assertJsonSerializable(value: unknown): void;
export declare class Session<TMetadata extends SessionMetadata = SessionMetadata> implements SessionTree {
    private readonly storage;
    readonly idGenerator: IdGenerator;
    constructor(storage: SessionStorage<TMetadata>, options?: {
        idGenerator?: IdGenerator;
    });
    getMetadata(): Promise<TMetadata>;
    view(lane: string): SessionTree;
    getLeafId(): Promise<string | null>;
    getEntry(id: string): Promise<Entry | undefined>;
    getStats(): Promise<SessionStats>;
    getName(): Promise<string | undefined>;
    setName(name: string | undefined): Promise<void>;
    getLabel(targetId: string): Promise<string | undefined>;
    setLabel(targetId: string, label: string | undefined): Promise<void>;
    findEntries(query?: EntryQuery): Promise<Entry[]>;
    findEntry(query?: EntryQuery): Promise<Entry | undefined>;
    findEntriesOnBranch(query?: EntryQuery & BranchBounds): Promise<Entry[]>;
    findEntryOnBranch(query?: EntryQuery & BranchBounds): Promise<Entry | undefined>;
    appendMessage(message: AgentMessage): Promise<string>;
    appendCustomEntry(customType: string, data?: unknown): Promise<string>;
    getLanes(): Promise<LanePointer[]>;
    createLane(lane: string, at: string | null): Promise<void>;
    moveLane(lane: string, to: string | null): Promise<void>;
    appendEntry<TEntry extends Entry>(entry: ProvisionedEntry<TEntry>, lane: string): Promise<TEntry>;
    appendRecord<TNewRecord extends NewRecord>(record: TNewRecord): Promise<TNewRecord & Pick<RecordBase, "seq" | "timestamp">>;
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
    private getLeafIdForLane;
    private queryEntries;
    private queryBranchEntries;
    private queryRecords;
    private queryLog;
    private appendMessageToLane;
    private appendCustomEntryToLane;
    private commitEntry;
    private commitRecord;
}
//# sourceMappingURL=session.d.ts.map
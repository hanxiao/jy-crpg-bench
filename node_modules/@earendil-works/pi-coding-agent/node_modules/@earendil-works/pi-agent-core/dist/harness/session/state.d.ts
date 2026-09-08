import { type BranchBounds, type Entry, type EntryQuery, type ForkOptions, type LanePointer, type LaneRecord, type LogItem, type LogOptions, type OperationStartedRecord, type RecordQuery, type SessionStats } from "./types.ts";
export type SessionMutation = {
    kind: "entry";
    lane?: string;
    entry: Entry;
} | {
    kind: "record";
    record: LaneRecord;
} | {
    kind: "lane";
    seq: number;
    lane: string;
    leafId: string | null;
} | {
    kind: "fact";
    seq: number;
    fact: "name";
    name: string | undefined;
} | {
    kind: "fact";
    seq: number;
    fact: "label";
    targetId: string;
    label: string | undefined;
};
type InvalidMutation = (message: string) => never;
export declare class SessionState {
    private sequence;
    private readonly usedIds;
    private readonly entries;
    private readonly entriesById;
    private readonly records;
    private readonly openOperationsByLane;
    private readonly lanes;
    private readonly log;
    private readonly stats;
    private name;
    private readonly labels;
    get nextSequence(): number;
    getLanes(): LanePointer[];
    requireLane(lane: string): string | null;
    validateNewLane(lane: string): void;
    validateTarget(targetId: string | null): void;
    validateUnusedId(id: string): void;
    applyMutation(mutation: SessionMutation, invalid?: InvalidMutation): void;
    getEntry(id: string): Entry | undefined;
    findEntries(query?: EntryQuery): Entry[];
    findEntriesOnBranch(query: EntryQuery & BranchBounds & {
        start: string;
    }): Entry[];
    findRecords(query?: RecordQuery): LaneRecord[];
    findOpenOperations(lane: string, options?: {
        limit?: number;
    }): OperationStartedRecord[];
    getLog(options?: LogOptions): LogItem[];
    getName(): string | undefined;
    getLabel(id: string): string | undefined;
    getStats(): SessionStats;
    createForkMutations(options: ForkOptions): SessionMutation[];
    private walkToRoot;
    private matchesEntryQuery;
    private matchesRecordQuery;
}
export {};
//# sourceMappingURL=state.d.ts.map
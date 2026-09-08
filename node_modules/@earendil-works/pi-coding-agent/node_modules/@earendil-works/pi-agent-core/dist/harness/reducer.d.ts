import type { AssistantMessage, DeferredHandle, StopReason } from "@earendil-works/pi-ai";
import type { AgentMessage, AgentToolCall, ThinkingLevel } from "../types.ts";
import type { Entry, LaneRecord, OperationStartedRecord, ProvisionedEntry, ToolStartedRecord } from "./session/types.ts";
/**
 * Machine-readable category for a contradiction in a lane's durable recovery
 * slice. These indicate states the single-writer record protocol cannot
 * produce, not ordinary operation failures or incomplete-but-recoverable
 * intent/result prefixes. Restore must reject such states rather than repair or
 * continue it; the accompanying error message supplies human-readable detail.
 */
export type RecordLogCorruptionReason = "multiple_open_operations" | "unknown_operation" | "record_after_finish" | "non_consecutive_attempt" | "invalid_compaction_reason" | "queue_after_abort" | "invalid_queue_cancellation" | "inconsistent_step" | "tool_call_mismatch" | "duplicate_tool_invocation" | "provisioned_entry_mismatch" | "invalid_deferred_handle";
export declare class RecordLogCorruption extends Error {
    readonly reason: RecordLogCorruptionReason;
    constructor(reason: RecordLogCorruptionReason, message: string);
}
export interface RecordLogSlice {
    lane: string;
    openOperations: readonly OperationStartedRecord[];
    records: readonly LaneRecord[];
    /** Operation-owned entries plus entries fetched directly by provisioned or referenced ids. */
    entries: readonly Entry[];
}
export interface EffectiveLaneConfiguration {
    model: {
        provider: string;
        modelId: string;
    };
    thinkingLevel: ThinkingLevel;
    activeToolNames: string[];
}
export interface TerminalFailureState {
    entryId: string;
    source: "step" | "deferred_fetch";
    message: AssistantMessage;
}
export interface ToolBatchState {
    assistantEntryId: string;
    calls: {
        toolIndex: number;
        toolCall: AgentToolCall;
        started?: ToolStartedRecord;
        resultExists: boolean;
        terminate?: boolean;
    }[];
    truncated: boolean;
    unresolved: boolean;
}
export interface LaneState {
    lane: string;
    leafId: string | null;
    operation: null | {
        id: string;
        kind: "run" | "compaction" | "navigation";
        intent: OperationStartedRecord["intent"];
        aborting: boolean;
        step: null | {
            kind: "assistant" | "compaction" | "branch_summary";
            attempts: number;
            resultEntryId: string;
            compactionReason?: "manual" | "threshold" | "overflow";
        };
        toolBatch: ToolBatchState | null;
        missingInitialMessages: ProvisionedEntry[];
        pendingSteer: ProvisionedEntry[];
        pendingFollowUp: ProvisionedEntry[];
        pendingWrites: ProvisionedEntry[];
        deferred: DeferredHandle | null;
        overflowRecoveryUsed: boolean;
        newestOwn: null | {
            entryId: string;
            type: Entry["type"];
            role?: AgentMessage["role"];
            stopReason?: StopReason;
        };
        targets: {
            result?: boolean;
            summary?: boolean;
        };
    };
    pendingNextRun: ProvisionedEntry[];
}
export interface LaneReductionInput extends RecordLogSlice {
    leafId: string | null;
    /** Entries appended by the open operation, oldest first. Empty when idle. */
    ownEntries: readonly Entry[];
    /** Bounded effective-state lookups at the operation anchor or idle leaf, oldest first. */
    configurationEntries: readonly Entry[];
    /** Harness option fallbacks used when no persisted value exists. */
    defaults: EffectiveLaneConfiguration;
}
export interface LaneReductionResult {
    laneState: LaneState;
    effectiveConfiguration: EffectiveLaneConfiguration;
    terminalFailure: TerminalFailureState | null;
}
/** Validates a bounded lane recovery slice without reading or mutating session state. */
export declare function validateRecordLog(input: RecordLogSlice): void;
/** Purely reconstructs one lane's orchestration state from its bounded recovery inputs. */
export declare function reduceLaneState(input: LaneReductionInput): LaneReductionResult;
//# sourceMappingURL=reducer.d.ts.map
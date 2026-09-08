import type { Api, AssistantMessage, DeferredHandle, ImageContent, Message, Model, Models, RetryPolicy, SimpleStreamOptions, Usage } from "@earendil-works/pi-ai";
import type { AgentMessage, AgentTool, QueueMode, ThinkingLevel } from "../types.ts";
import type { CompactionSettings } from "./compaction/compaction.ts";
import { type Result as ResultValue } from "./result.ts";
import type { BranchSummaryEntry, CompactionEntry, Entry, JsonValue, ProvisionedEntry, Session, SessionTree } from "./session/index.ts";
import type { TelemetryContext } from "./telemetry.ts";
import type { AgentHarnessResources, PromptTemplate, Skill } from "./types.ts";
declare const LaneBusy_base: import("./result.ts").TaggedErrorFactory<"LaneBusy">;
export declare class LaneBusy extends LaneBusy_base<{
    lane: string;
    operationId: string;
    operationKind: "run" | "compaction" | "navigation";
    message: string;
}> {
}
declare const MissingIdentities_base: import("./result.ts").TaggedErrorFactory<"MissingIdentities">;
export declare class MissingIdentities extends MissingIdentities_base<{
    lane: string;
    tools: string[];
    models: string[];
    message: string;
}> {
}
declare const NoActiveRun_base: import("./result.ts").TaggedErrorFactory<"NoActiveRun">;
export declare class NoActiveRun extends NoActiveRun_base<{
    lane: string;
    message: string;
}> {
}
declare const NoActiveOperation_base: import("./result.ts").TaggedErrorFactory<"NoActiveOperation">;
export declare class NoActiveOperation extends NoActiveOperation_base<{
    lane: string;
    message: string;
}> {
}
declare const NothingToResume_base: import("./result.ts").TaggedErrorFactory<"NothingToResume">;
export declare class NothingToResume extends NothingToResume_base<{
    lane: string;
    message: string;
}> {
}
declare const InvalidMessage_base: import("./result.ts").TaggedErrorFactory<"InvalidMessage">;
export declare class InvalidMessage extends InvalidMessage_base<{
    lane: string;
    reason: string;
    message: string;
}> {
}
declare const UnknownSkill_base: import("./result.ts").TaggedErrorFactory<"UnknownSkill">;
export declare class UnknownSkill extends UnknownSkill_base<{
    name: string;
    message: string;
}> {
}
declare const UnknownTemplate_base: import("./result.ts").TaggedErrorFactory<"UnknownTemplate">;
export declare class UnknownTemplate extends UnknownTemplate_base<{
    name: string;
    message: string;
}> {
}
declare const UnknownTarget_base: import("./result.ts").TaggedErrorFactory<"UnknownTarget">;
export declare class UnknownTarget extends UnknownTarget_base<{
    targetId: string;
    message: string;
}> {
}
declare const UnknownQueueItem_base: import("./result.ts").TaggedErrorFactory<"UnknownQueueItem">;
export declare class UnknownQueueItem extends UnknownQueueItem_base<{
    lane: string;
    entryId: string;
    message: string;
}> {
}
declare const LaneExists_base: import("./result.ts").TaggedErrorFactory<"LaneExists">;
export declare class LaneExists extends LaneExists_base<{
    lane: string;
    message: string;
}> {
}
declare const InvalidLane_base: import("./result.ts").TaggedErrorFactory<"InvalidLane">;
export declare class InvalidLane extends InvalidLane_base<{
    lane: string;
    reason: string;
    message: string;
}> {
}
declare const NothingToCompact_base: import("./result.ts").TaggedErrorFactory<"NothingToCompact">;
export declare class NothingToCompact extends NothingToCompact_base<{
    lane: string;
    message: string;
}> {
}
declare const Closed_base: import("./result.ts").TaggedErrorFactory<"Closed">;
export declare class Closed extends Closed_base<{
    message: string;
}> {
}
export declare class HarnessFault extends Error {
    readonly cause: unknown;
    constructor(message: string, cause: unknown);
}
export declare class HarnessClosed extends Error {
    constructor();
}
export declare class HarnessNotImplemented extends Error {
    readonly operation: string;
    constructor(operation: string);
}
export interface OperationError {
    code: string;
    message: string;
}
export type RunOutcome = {
    kind: "completed";
    leafId: string;
    finalEntryId: string;
    finalMessage: AssistantMessage;
} | {
    kind: "aborted";
    leafId: string;
    finalEntryId: string;
    finalMessage: AssistantMessage;
} | {
    kind: "failed";
    leafId: string;
    error: OperationError;
    finalEntryId?: string;
    finalMessage?: AssistantMessage;
} | {
    kind: "suspended";
    leafId: string;
    finalEntryId: string;
    deferred: DeferredHandle;
};
export type CompactionOutcome = {
    kind: "completed";
    leafId: string;
    entry: CompactionEntry;
} | {
    kind: "declined" | "aborted";
    leafId: string;
} | {
    kind: "failed";
    leafId: string;
    error: OperationError;
};
export type NavigationOutcome = {
    kind: "completed";
    newLeafId: string | null;
    summaryEntry?: BranchSummaryEntry;
} | {
    kind: "declined" | "aborted";
    leafId: string | null;
} | {
    kind: "failed";
    leafId: string | null;
    error: OperationError;
};
export type RunRejected = LaneBusy | InvalidMessage | UnknownSkill | UnknownTemplate | Closed;
export type CompactionRejected = LaneBusy | NothingToCompact | Closed;
export type NavigationRejected = LaneBusy | UnknownTarget | Closed;
export type ResumeRejected = LaneBusy | NothingToResume | MissingIdentities | Closed;
export type QueueRejected = NoActiveRun | InvalidMessage | Closed;
export type CancelQueuedRejected = UnknownQueueItem | Closed;
export type AbortRejected = NoActiveOperation | Closed;
export type RunResult = ResultValue<{
    runId: string;
} & RunOutcome, RunRejected>;
export type CompactionResult = ResultValue<{
    runId: string;
} & CompactionOutcome, CompactionRejected>;
export type NavigationResult = ResultValue<{
    runId: string;
} & NavigationOutcome, NavigationRejected>;
export type QueueResult = ResultValue<{
    entryId: string;
}, QueueRejected>;
export type CancelQueuedResult = ResultValue<{
    outcome: "cancelled" | "already_consumed" | "already_cleared";
}, CancelQueuedRejected>;
export type RecordUsageResult = ResultValue<void, Closed>;
export type AbortResult = ResultValue<{
    runId: string;
    steer: AgentMessage[];
    followUp: AgentMessage[];
}, AbortRejected>;
export type ResumeOutcome = ({
    operation: "run";
    runId: string;
} & RunOutcome) | ({
    operation: "compaction";
    runId: string;
} & CompactionOutcome) | ({
    operation: "navigation";
    runId: string;
} & NavigationOutcome);
export type ResumeResult = ResultValue<ResumeOutcome, ResumeRejected>;
export type CreateLaneResult = ResultValue<AgentLane, LaneExists | InvalidLane | UnknownTarget | Closed>;
export interface NavigateOptions {
    summarize?: boolean;
    customInstructions?: string;
    label?: string;
}
export interface SuspendedOperation {
    lane: string;
    kind: "run" | "compaction" | "navigation";
    id: string;
    startedAt: number;
    reason: "crash" | "deferred";
    prompt?: AgentMessage[];
    deferred?: DeferredHandle;
    aborting?: {
        steer: AgentMessage[];
        followUp: AgentMessage[];
    };
    missing: {
        tools: string[];
        models: string[];
    };
}
export interface LaneInfo {
    name: string;
    leafId: string | null;
    operation: null | {
        id: string;
        kind: "run" | "compaction" | "navigation";
        status: "running" | "suspended" | "aborting";
    };
}
export interface QueuedItem {
    entryId: string;
    message: AgentMessage;
}
export interface LaneSnapshot {
    lane: string;
    transcript: Entry[];
    leafId: string | null;
    operation: LaneInfo["operation"];
    queues: {
        steer: QueuedItem[];
        followUp: QueuedItem[];
        nextRun: QueuedItem[];
    };
    pendingWrites: {
        id: string;
        entry: ProvisionedEntry;
    }[];
    faulted: boolean;
}
export interface SessionSnapshot {
    lanes: (LaneInfo & {
        suspended?: SuspendedOperation;
    })[];
    faulted: boolean;
}
export type ActionInfo = {
    kind: "append_entry";
    entryType: Entry["type"];
    entryId: string;
} | {
    kind: "append_record";
    recordType: string;
} | {
    kind: "move_lane";
    to: string | null;
} | {
    kind: "set_fact";
    fact: "name" | "label";
} | {
    kind: "try_finish_run";
    outcome: "completed" | "failed";
} | {
    kind: "finish_operation";
    outcome: "completed" | "declined" | "failed" | "aborted";
} | {
    kind: "commit_follow_up";
} | {
    kind: "consume_queue_item";
    queue: "steer" | "followUp";
    entryId: string;
} | {
    kind: "apply_pending_write";
    entryId: string;
} | {
    kind: "stream_assistant";
    step: "assistant" | "compaction" | "branch_summary";
    attempt: number;
} | {
    kind: "execute_tool";
    toolCallId: string;
    toolName: string;
} | {
    kind: "fetch_deferred" | "cancel_deferred";
    provider: string;
    id: string;
} | {
    kind: "hook";
    name: HookName;
} | {
    kind: "sleep";
    delayMs: number;
};
export type HookName = "before_run" | "before_resume" | "before_run_end" | "transform_context" | "before_request" | "before_payload" | "after_response" | "before_tool" | "after_tool" | "before_compaction" | "before_navigation";
export interface Hooks {
    on(name: HookName, handler: (event: unknown) => unknown | Promise<unknown>, options?: {
        id?: string;
    }): () => void;
}
export interface Events {
    on(type: string, listener: (event: unknown) => void | Promise<void>): () => void;
}
export type HarnessTool = AgentTool & {
    replay?: "never" | "safe";
};
export type Resources = AgentHarnessResources<Skill, PromptTemplate>;
export type StreamOptions = SimpleStreamOptions;
export type StreamOptionsPatch = Partial<SimpleStreamOptions>;
export type EntryProjector = (entry: Entry) => AgentMessage[] | Promise<AgentMessage[]>;
export interface AgentHarnessOptions {
    session: Session;
    models: Models;
    model: Model<Api>;
    thinkingLevel?: ThinkingLevel;
    activeToolNames?: string[];
    tools?: HarnessTool[];
    toolContext?: object | (() => object | Promise<object>);
    systemPrompt?: string | (() => string | Promise<string>);
    resources?: Resources;
    streamOptions?: StreamOptions;
    retry?: RetryPolicy;
    compaction?: CompactionSettings;
    steeringMode?: QueueMode;
    followUpMode?: QueueMode;
    toolExecution?: "sequential" | "parallel";
    drive?: "automatic" | "manual";
    toProviderMessages?: (messages: AgentMessage[]) => Message[] | Promise<Message[]>;
    entryProjectors?: Record<string, EntryProjector>;
    context?: TelemetryContext;
}
export interface WatchHandle<TSnapshot> {
    snapshot: TSnapshot;
    start(listener: (event: unknown) => void): void;
    unsubscribe(): void;
}
export interface AgentLane {
    readonly name: string;
    getLeafId(): Promise<string | null>;
    prompt(text: string, images?: ImageContent[]): Promise<RunResult>;
    prompt(message: AgentMessage | AgentMessage[]): Promise<RunResult>;
    skill(name: string, additionalInstructions?: string): Promise<RunResult>;
    promptFromTemplate(name: string, args?: string[]): Promise<RunResult>;
    compact(options?: {
        customInstructions?: string;
    }): Promise<CompactionResult>;
    navigateTree(targetId: string | null, options?: NavigateOptions): Promise<NavigationResult>;
    resume(): Promise<ResumeResult>;
    abort(): Promise<AbortResult>;
    steer(text: string, images?: ImageContent[]): Promise<QueueResult>;
    steer(message: AgentMessage): Promise<QueueResult>;
    followUp(text: string, images?: ImageContent[]): Promise<QueueResult>;
    followUp(message: AgentMessage): Promise<QueueResult>;
    nextRun(text: string, images?: ImageContent[]): Promise<QueueResult>;
    nextRun(message: AgentMessage): Promise<QueueResult>;
    cancelQueued(entryId: string): Promise<CancelQueuedResult>;
    recordUsage(usage: Usage, options?: {
        entryId?: string;
        details?: JsonValue;
    }): Promise<RecordUsageResult>;
    waitForIdle(): Promise<void>;
    runWhenIdle(callback: () => void | Promise<void>): Promise<void>;
    peekAction(): Promise<ActionInfo | undefined>;
    executeAction(): Promise<ActionInfo | undefined>;
    runToCompletion(): Promise<void>;
    getModel(): Promise<Model<Api>>;
    setModel(model: Model<Api>): Promise<void>;
    getThinkingLevel(): Promise<ThinkingLevel>;
    setThinkingLevel(level: ThinkingLevel): Promise<void>;
    getActiveTools(): Promise<string[]>;
    setActiveTools(names: string[]): Promise<void>;
    readonly session: SessionTree;
    watch(): Promise<WatchHandle<LaneSnapshot>>;
}
export declare class AgentHarness implements AgentLane {
    readonly name = "main";
    readonly session: SessionTree;
    readonly hooks: Hooks;
    readonly events: Events;
    private readonly durableSession;
    private model;
    private thinkingLevel;
    private activeToolNames;
    private tools;
    private resources;
    private streamOptions;
    private retryPolicy;
    private compactionSettings;
    private steeringMode;
    private followUpMode;
    private closed;
    private constructor();
    static create(options: AgentHarnessOptions): Promise<{
        harness: AgentHarness;
        suspended: SuspendedOperation[];
    }>;
    private unavailable;
    getLeafId(): Promise<string | null>;
    prompt(_text: string, _images?: ImageContent[]): Promise<RunResult>;
    prompt(_message: AgentMessage | AgentMessage[]): Promise<RunResult>;
    skill(_name: string, _additionalInstructions?: string): Promise<RunResult>;
    promptFromTemplate(_name: string, _args?: string[]): Promise<RunResult>;
    compact(_options?: {
        customInstructions?: string;
    }): Promise<CompactionResult>;
    navigateTree(_targetId: string | null, _options?: NavigateOptions): Promise<NavigationResult>;
    resume(): Promise<ResumeResult>;
    abort(): Promise<AbortResult>;
    steer(_text: string, _images?: ImageContent[]): Promise<QueueResult>;
    steer(_message: AgentMessage): Promise<QueueResult>;
    followUp(_text: string, _images?: ImageContent[]): Promise<QueueResult>;
    followUp(_message: AgentMessage): Promise<QueueResult>;
    nextRun(_text: string, _images?: ImageContent[]): Promise<QueueResult>;
    nextRun(_message: AgentMessage): Promise<QueueResult>;
    cancelQueued(_entryId: string): Promise<CancelQueuedResult>;
    recordUsage(_usage: Usage, _options?: {
        entryId?: string;
        details?: JsonValue;
    }): Promise<RecordUsageResult>;
    waitForIdle(): Promise<void>;
    runWhenIdle(_callback: () => void | Promise<void>): Promise<void>;
    peekAction(): Promise<ActionInfo | undefined>;
    executeAction(): Promise<ActionInfo | undefined>;
    runToCompletion(): Promise<void>;
    getModel(): Promise<Model<Api>>;
    setModel(model: Model<Api>): Promise<void>;
    getThinkingLevel(): Promise<ThinkingLevel>;
    setThinkingLevel(level: ThinkingLevel): Promise<void>;
    getActiveTools(): Promise<string[]>;
    setActiveTools(names: string[]): Promise<void>;
    watch(): Promise<WatchHandle<LaneSnapshot>>;
    lane(_name: string): Promise<AgentLane | undefined>;
    createLane(_name: string, _at: string | null): Promise<CreateLaneResult>;
    lanes(): Promise<LaneInfo[]>;
    getTools(): Promise<HarnessTool[]>;
    setTools(tools: HarnessTool[], activeNames?: string[]): Promise<void>;
    getResources(): Promise<Resources>;
    setResources(resources: Resources): Promise<void>;
    getStreamOptions(): Promise<StreamOptions>;
    setStreamOptions(options: StreamOptions): Promise<void>;
    getRetryPolicy(): Promise<RetryPolicy>;
    setRetryPolicy(policy: RetryPolicy): Promise<void>;
    getCompactionSettings(): Promise<CompactionSettings>;
    setCompactionSettings(settings: CompactionSettings): Promise<void>;
    getSteeringMode(): Promise<QueueMode>;
    setSteeringMode(mode: QueueMode): Promise<void>;
    getFollowUpMode(): Promise<QueueMode>;
    setFollowUpMode(mode: QueueMode): Promise<void>;
    watchSession(): Promise<WatchHandle<SessionSnapshot>>;
    close(): Promise<void>;
}
export {};
//# sourceMappingURL=agent-harness.d.ts.map
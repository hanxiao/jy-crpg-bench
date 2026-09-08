import type { AgentMessage } from "../../types.ts";
import type { CustomEntry, Entry } from "./types.ts";
export interface SessionContext {
    messages: AgentMessage[];
    thinkingLevel: string;
    model: {
        provider: string;
        modelId: string;
    } | null;
    activeToolNames: string[] | null;
}
export type ContextEntryTransform = (entries: readonly Entry[]) => readonly Entry[];
export type CustomEntryContextMessageProjector = (entry: CustomEntry, index: number, entries: readonly Entry[]) => readonly AgentMessage[] | undefined;
export interface SessionContextBuildOptions {
    entryTransforms?: readonly ContextEntryTransform[];
    entryProjectors?: Readonly<Record<string, CustomEntryContextMessageProjector>>;
}
export declare function defaultContextEntryTransform(pathEntries: readonly Entry[]): Entry[];
export declare function buildContextEntries(pathEntries: readonly Entry[], options?: SessionContextBuildOptions): Entry[];
export declare function sessionEntryToContextMessages(entry: Entry, index: number, entries: readonly Entry[], options?: SessionContextBuildOptions): AgentMessage[];
export declare function buildSessionContext(pathEntries: readonly Entry[], options?: SessionContextBuildOptions): SessionContext;
//# sourceMappingURL=context.d.ts.map
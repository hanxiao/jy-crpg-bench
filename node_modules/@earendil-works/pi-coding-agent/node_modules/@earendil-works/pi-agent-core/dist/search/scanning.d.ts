import type { Entry, SessionMetadata, SessionStorage } from "../harness/session/types.ts";
import type { SessionSearch, SessionSearchHit, SessionSearchOptions } from "./index.ts";
export interface SessionSearchCandidate {
    readonly entryId: string;
    readonly seq: number;
    readonly type: Entry["type"];
    readonly timestamp: number;
    readonly text: string;
    readonly fields?: Record<string, unknown>;
}
export type ScanningReadable<TMetadata extends SessionMetadata = SessionMetadata> = Pick<SessionStorage<TMetadata>, "getMetadata" | "findEntries" | "getLabel">;
export type ScanningReadableSource<TMetadata extends SessionMetadata = SessionMetadata, TOptions = unknown> = (options?: TOptions) => AsyncIterable<ScanningReadable<TMetadata>>;
export type ScanningSearchTextProjector<TMetadata extends SessionMetadata = SessionMetadata> = (metadata: TMetadata, entry: Entry, label: string | undefined) => string;
export interface ScanningReadableOptions<TMetadata extends SessionMetadata = SessionMetadata> {
    projectText?: ScanningSearchTextProjector<TMetadata>;
    pageSize?: number;
}
export interface ScanningSessionSearchHit extends SessionSearchHit {
    readonly timestamp: number;
    readonly snippet: string;
}
export interface ScanningSessionSearchOptions<TMetadata extends SessionMetadata = SessionMetadata, TSourceOptions = unknown, THit extends SessionSearchHit = ScanningSessionSearchHit> extends ScanningReadableOptions<TMetadata> {
    sourceOptions?: (text: string, options: SessionSearchOptions) => TSourceOptions | undefined;
    match?: (queryText: string, candidate: SessionSearchCandidate, metadata: TMetadata) => boolean;
    createHit?: (metadata: TMetadata, candidate: SessionSearchCandidate) => THit;
}
export declare function scanningEntries<TMetadata extends SessionMetadata>(readable: ScanningReadable<TMetadata>, options?: ScanningReadableOptions<TMetadata>): AsyncIterable<SessionSearchCandidate>;
export declare function createScanningSessionSearch<TMetadata extends SessionMetadata, TSourceOptions = unknown, THit extends SessionSearchHit = ScanningSessionSearchHit>(source: readonly ScanningReadable<TMetadata>[] | ScanningReadableSource<TMetadata, TSourceOptions>, options?: ScanningSessionSearchOptions<TMetadata, TSourceOptions, THit>): SessionSearch<THit>;
//# sourceMappingURL=scanning.d.ts.map
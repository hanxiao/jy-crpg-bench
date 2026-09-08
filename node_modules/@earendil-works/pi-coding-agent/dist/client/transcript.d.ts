import type { SessionSnapshot, TranscriptItem, TranscriptProgress } from "@earendil-works/pi-protocol";
export interface TranscriptState {
    readonly snapshot: SessionSnapshot;
    readonly progressItems: ReadonlyMap<string, TranscriptItem>;
    readonly progressOrder: readonly string[];
    readonly toolCallBuffers: ReadonlyMap<string, string>;
}
export declare function createTranscriptState(snapshot: SessionSnapshot): TranscriptState;
export declare function applyTranscriptSnapshot(state: TranscriptState, snapshot: SessionSnapshot): TranscriptState;
export declare function applyTranscriptProgress(state: TranscriptState, progress: TranscriptProgress): TranscriptState;
export declare function selectTranscript(state: TranscriptState): readonly TranscriptItem[];
//# sourceMappingURL=transcript.d.ts.map
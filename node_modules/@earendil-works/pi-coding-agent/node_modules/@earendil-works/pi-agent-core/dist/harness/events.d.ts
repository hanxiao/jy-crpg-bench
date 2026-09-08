export interface RunStartEvent {
    type: "run_start";
    lane: string;
    runId: string;
}
export interface RunEndEvent {
    type: "run_end";
    lane: string;
    runId: string;
    outcome: "completed" | "aborted" | "failed";
    leafId: string;
}
export type HarnessEvent = RunStartEvent | RunEndEvent;
export type HarnessEventType = HarnessEvent["type"];
export type HarnessEventOfType<TType extends HarnessEventType> = Extract<HarnessEvent, {
    type: TType;
}>;
export type HarnessEventListener<TEvent extends HarnessEvent = HarnessEvent> = (event: TEvent) => void | Promise<void>;
export interface Events {
    /**
     * Register a passive listener for future events and return its unsubscribe function.
     * Earlier events are not replayed and no current-state snapshot is provided; use a lane or session watch for both.
     */
    on<TType extends HarnessEventType>(type: TType, listener: HarnessEventListener<HarnessEventOfType<TType>>): () => void;
}
export interface WatchHandle<TSnapshot> {
    snapshot: TSnapshot;
    start(listener: HarnessEventListener): void;
    unsubscribe(): void;
}
export declare class HarnessEventBus implements Events {
    private readonly listeners;
    private readonly watchListeners;
    /**
     * Register a listener for future events of one type and return its unsubscribe function.
     * Earlier events are not replayed, and no snapshot or event buffer is provided.
     */
    on<TType extends HarnessEventType>(type: TType, listener: HarnessEventListener<HarnessEventOfType<TType>>): () => void;
    /** Publish an event to current event subscriptions and watch subscriptions. */
    emit(event: HarnessEvent): void;
    watch<TSnapshot>(captureSnapshot: () => TSnapshot): WatchHandle<TSnapshot>;
}
//# sourceMappingURL=events.d.ts.map
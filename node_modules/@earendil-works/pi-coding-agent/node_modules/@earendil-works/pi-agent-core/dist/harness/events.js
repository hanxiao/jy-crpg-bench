export class HarnessEventBus {
    listeners = new Map();
    watchListeners = new Set();
    /**
     * Register a listener for future events of one type and return its unsubscribe function.
     * Earlier events are not replayed, and no snapshot or event buffer is provided.
     */
    on(type, listener) {
        // Reuse this event type's listener set, or create its first set.
        const listeners = this.listeners.get(type) ?? new Set();
        this.listeners.set(type, listeners);
        // Wrap this event-specific callback so it can be stored as a general HarnessEvent listener.
        // Keep the wrapper reference so unsubscribe can remove that exact function from the set.
        const receive = (event) => {
            if (event.type === type)
                return listener(event);
        };
        listeners.add(receive);
        return () => {
            listeners.delete(receive);
            if (listeners.size === 0)
                this.listeners.delete(type);
        };
    }
    /** Publish an event to current event subscriptions and watch subscriptions. */
    emit(event) {
        // Deliver only to direct listeners registered for this event type.
        // Async results are not awaited because emit() is synchronous.
        for (const listener of this.listeners.get(event.type) ?? [])
            void listener(event);
        // Deliver every event to each watcher; watch() handles buffering until start().
        for (const listener of this.watchListeners)
            listener(event);
    }
    watch(captureSnapshot) {
        let listener;
        let buffered = [];
        const receive = (event) => {
            if (listener)
                void listener(event);
            else
                buffered.push(event);
        };
        this.watchListeners.add(receive);
        const snapshot = captureSnapshot();
        return {
            snapshot,
            start: (nextListener) => {
                // Stay in buffering mode while flushing so reentrant emissions preserve order.
                while (buffered.length > 0) {
                    const pending = buffered;
                    buffered = [];
                    for (const event of pending)
                        void nextListener(event);
                }
                listener = nextListener;
            },
            unsubscribe: () => {
                this.watchListeners.delete(receive);
                buffered = [];
            },
        };
    }
}
//# sourceMappingURL=events.js.map
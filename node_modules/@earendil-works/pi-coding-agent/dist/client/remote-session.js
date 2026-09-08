import { applyTranscriptProgress, applyTranscriptSnapshot, createTranscriptState, selectTranscript, } from "./transcript.js";
class RemoteSessionDisposedError extends Error {
    constructor() {
        super("Remote session is disposed");
        this.name = "RemoteSessionDisposedError";
    }
}
async function settleRemoteSessionDisposal(cleanup) {
    const results = await Promise.allSettled(cleanup);
    const errors = results.flatMap((result) => result.status === "rejected" && !(result.reason instanceof RemoteSessionDisposedError) ? [result.reason] : []);
    if (errors.length === 1)
        throw errors[0];
    if (errors.length > 1)
        throw new AggregateError(errors, "Failed to dispose remote session");
}
export class RemoteSession {
    #client;
    #onListenerError;
    #lifecycle = { status: "unbound" };
    #handle;
    #transcript;
    #unsubscribeSnapshot;
    #unsubscribeEvents;
    #listeners = new Set();
    #pendingAttachmentOperations = new Set();
    #activeOperationStates = new Set();
    #disposePromise;
    #resolveDisposeSignal = () => { };
    #disposeSignal = new Promise((resolve) => {
        this.#resolveDisposeSignal = resolve;
    });
    constructor(client, options = {}) {
        this.#client = client;
        this.#onListenerError = options.onListenerError;
    }
    get id() {
        return this.#handle?.id;
    }
    get state() {
        return {
            lifecycle: this.#lifecycle,
            snapshot: this.#transcript?.snapshot,
            transcript: this.#transcript ? selectTranscript(this.#transcript) : [],
        };
    }
    get snapshot() {
        return this.#transcript?.snapshot;
    }
    get phase() {
        return this.snapshot?.phase;
    }
    get operation() {
        return this.#lifecycle.status === "busy" ? this.#lifecycle.operation : undefined;
    }
    get models() {
        return this.#client.snapshot?.models ?? [];
    }
    get sessions() {
        return this.#client.snapshot?.sessions ?? [];
    }
    get connectionState() {
        return this.#client.connectionState;
    }
    get disposed() {
        return this.#lifecycle.status === "disposed";
    }
    subscribe(listener) {
        this.#assertNotDisposed();
        this.#listeners.add(listener);
        this.#callListener(listener, this.state);
        return () => this.#listeners.delete(listener);
    }
    onConnectionStateChange(listener) {
        this.#assertNotDisposed();
        return this.#client.onConnectionStateChange(listener);
    }
    static async open(client, sessionId, options = {}) {
        const session = new RemoteSession(client, options);
        try {
            await session.open(sessionId);
            return session;
        }
        catch (error) {
            await session.dispose();
            throw error;
        }
    }
    async open(sessionId) {
        if (this.#handle?.id === sessionId && this.#lifecycle.status === "ready")
            return;
        await this.#replace("open", () => this.#client.acquireSession(sessionId, { mode: "exclusive" }));
    }
    static async create(client, createOptions, options = {}) {
        const session = new RemoteSession(client, options);
        try {
            await session.create(createOptions);
            return session;
        }
        catch (error) {
            await session.dispose();
            throw error;
        }
    }
    async create(options) {
        await this.#replace("create", () => this.#client.createSession(options));
    }
    async submit(text) {
        const normalized = text.trim();
        if (!normalized)
            return;
        this.#assertAvailable();
        const handle = this.#requireHandle();
        if (this.phase !== "idle" && this.phase !== "turn") {
            throw new Error(`Session cannot accept input during ${this.phase ?? "unknown"} phase`);
        }
        await this.#runOperation("submit", () => (this.phase === "idle" ? handle.prompt(normalized) : handle.steer(normalized)).then(() => undefined));
    }
    async abort() {
        const preemptingSubmit = this.#lifecycle.status === "busy" && this.#lifecycle.operation === "submit";
        if (preemptingSubmit)
            this.#assertNotDisposed();
        else
            this.#assertAvailable();
        const handle = this.#requireHandle();
        if (this.phase === "idle" && !preemptingSubmit)
            return;
        await this.#runOperation("abort", () => handle.abort().then(() => undefined), preemptingSubmit);
    }
    async setModel(model) {
        await this.#runIdleOperation("setModel", "change model", () => this.#requireHandle()
            .setModel(model)
            .then(() => undefined));
    }
    async setThinking(thinkingLevel) {
        await this.#runIdleOperation("setThinking", "change thinking level", () => this.#requireHandle()
            .setThinking(thinkingLevel)
            .then(() => undefined));
    }
    async reconnect() {
        this.#assertAvailable();
        const sessionId = this.#requireHandle().id;
        await this.#runOperation("reconnect", () => this.#trackAttachmentOperation(async () => {
            await this.#client.reconnect();
            const handle = await this.#client.acquireSession(sessionId, { mode: "exclusive" });
            await this.#assertNotDisposedAfterAwait(handle);
            this.#bind(handle);
        }));
    }
    dispose() {
        if (this.#disposePromise)
            return this.#disposePromise;
        const handle = this.#handle;
        this.#lifecycle = { status: "disposed" };
        this.#resolveDisposeSignal();
        this.#clearSubscriptions();
        this.#handle = undefined;
        this.#transcript = undefined;
        const cleanup = [...this.#pendingAttachmentOperations];
        if (handle)
            cleanup.push(handle.dispose());
        this.#disposePromise = settleRemoteSessionDisposal(cleanup);
        this.#notify();
        this.#listeners.clear();
        return this.#disposePromise;
    }
    [Symbol.asyncDispose]() {
        return this.dispose();
    }
    async #replace(operation, prepare) {
        this.#assertAvailable();
        if (this.#handle && this.phase !== "idle") {
            throw new Error(`Cannot ${operation} a session while session is ${this.phase ?? "unavailable"}`);
        }
        await this.#runOperation(operation, () => this.#trackAttachmentOperation(() => this.#prepareReplacement(operation, prepare)));
    }
    async #trackAttachmentOperation(run) {
        const pending = run();
        this.#pendingAttachmentOperations.add(pending);
        try {
            await pending;
        }
        finally {
            this.#pendingAttachmentOperations.delete(pending);
        }
    }
    async #prepareReplacement(operation, prepare) {
        const previous = this.#handle;
        const next = await prepare();
        await this.#assertNotDisposedAfterAwait(next);
        const snapshot = next.snapshot;
        if (!snapshot) {
            await this.#detach(next);
            throw new Error(`Session ${next.id} did not provide a snapshot`);
        }
        if (previous && previous.id !== next.id && previous.attached && this.phase !== "idle") {
            await this.#detach(next);
            throw new Error(`Cannot ${operation} a session while session is ${this.phase ?? "unavailable"}`);
        }
        if (previous && previous.id !== next.id && previous.attached) {
            try {
                await previous.detach();
            }
            catch (error) {
                try {
                    await this.#detach(next);
                }
                catch (cleanupError) {
                    throw new AggregateError([error, cleanupError], "Failed to replace remote session attachment");
                }
                throw error;
            }
        }
        await this.#assertNotDisposedAfterAwait(next);
        this.#bind(next, snapshot);
    }
    async #runIdleOperation(operation, description, run) {
        this.#assertAvailable();
        this.#requireHandle();
        if (this.phase !== "idle") {
            throw new Error(`Cannot ${description} while session is ${this.phase ?? "unavailable"}`);
        }
        await this.#runOperation(operation, run);
    }
    async #runOperation(operation, run, preempt = false) {
        if (preempt)
            this.#assertNotDisposed();
        else
            this.#assertAvailable();
        const previous = this.#lifecycle;
        const busy = { status: "busy", operation };
        this.#lifecycle = busy;
        this.#activeOperationStates.add(busy);
        this.#notify();
        const running = run();
        try {
            await Promise.race([
                running,
                this.#disposeSignal.then(() => {
                    throw new Error("Remote session is disposed");
                }),
            ]);
        }
        finally {
            this.#activeOperationStates.delete(busy);
            if (!this.disposed && this.#lifecycle === busy) {
                this.#lifecycle =
                    preempt && this.#activeOperationStates.has(previous)
                        ? previous
                        : this.#handle
                            ? { status: "ready" }
                            : { status: "unbound" };
                this.#notify();
            }
        }
    }
    #bind(handle, knownSnapshot) {
        const snapshot = knownSnapshot ?? handle.snapshot;
        if (!snapshot)
            throw new Error(`Session ${handle.id} did not provide a snapshot`);
        this.#clearSubscriptions();
        this.#handle = handle;
        this.#transcript = createTranscriptState(snapshot);
        this.#unsubscribeSnapshot = handle.subscribe((next) => {
            if (!this.#transcript)
                return;
            this.#transcript = applyTranscriptSnapshot(this.#transcript, next);
            this.#notify();
        });
        this.#unsubscribeEvents = handle.onEvent((event) => this.#handleEvent(event));
    }
    #handleEvent(event) {
        if (event.type === "session_removed") {
            this.#clearSubscriptions();
            this.#handle = undefined;
            this.#transcript = undefined;
            if (this.#lifecycle.status !== "busy")
                this.#lifecycle = { status: "unbound" };
            this.#notify();
            return;
        }
        if (event.type !== "session_progress" || !this.#transcript)
            return;
        this.#transcript = applyTranscriptProgress(this.#transcript, event.progress);
        this.#notify();
    }
    #notify() {
        const state = this.state;
        for (const listener of this.#listeners)
            this.#callListener(listener, state);
    }
    #callListener(listener, state) {
        try {
            listener(state);
        }
        catch (error) {
            this.#reportListenerError(error);
        }
    }
    #reportListenerError(error) {
        if (!this.#onListenerError)
            return;
        try {
            this.#onListenerError(error instanceof Error ? error : new Error(String(error)));
        }
        catch {
            // Diagnostics cannot affect session or transport state.
        }
    }
    #clearSubscriptions() {
        this.#unsubscribeSnapshot?.();
        this.#unsubscribeEvents?.();
        this.#unsubscribeSnapshot = undefined;
        this.#unsubscribeEvents = undefined;
    }
    #requireHandle() {
        if (!this.#handle)
            throw new Error("No remote session is attached");
        return this.#handle;
    }
    #assertAvailable() {
        this.#assertNotDisposed();
        if (this.#lifecycle.status === "busy") {
            throw new Error(`Remote session is busy with ${this.#lifecycle.operation}`);
        }
    }
    #assertNotDisposed() {
        if (this.disposed)
            throw new Error("Remote session is disposed");
    }
    async #assertNotDisposedAfterAwait(handle) {
        if (!this.disposed)
            return;
        await this.#detach(handle);
        throw new RemoteSessionDisposedError();
    }
    async #detach(handle) {
        await handle.dispose();
    }
}
//# sourceMappingURL=remote-session.js.map
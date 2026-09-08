import { encodeClientMessage, ProtocolValidationError, } from "@earendil-works/pi-protocol";
import { Connection } from "./connection.js";
import { PiClientDisposedError, PiDisconnectedError, PiServerError, PiSessionDetachedError, PiSessionOwnershipError, toError, } from "./errors.js";
import { createPromiseResolvers } from "./promise.js";
import { SessionHandle, } from "./session-handle.js";
import { ClientState } from "./state.js";
export class PiClient {
    #options;
    #connection;
    #state;
    #pendingRequests = new Map();
    #sessionLeaseCounts = new Map();
    #exclusiveSessionLeases = new Map();
    #sessionLeaseGenerations = new Map();
    #sessionAttachments = new Map();
    #sessionDetachments = new Map();
    #sessionCleanupRequired = new Set();
    #sessionReconciliations = new Map();
    #connectionStateListeners = new Set();
    #requestSequence = 0;
    #disposed = false;
    #disposePromise;
    constructor(options) {
        this.#options = options;
        this.#state = new ClientState(options.onListenerError);
        this.#connection = new Connection({
            transportFactory: options.transportFactory,
            maxFrameLength: options.maxFrameLength,
            onHandshake: (snapshot) => this.#state.applyServerSnapshot(snapshot),
            onMessage: (message) => this.#handleMessage(message),
            onStateChange: (change) => this.#handleConnectionStateChange(change),
        });
    }
    get disposed() {
        return this.#disposed;
    }
    get connectionState() {
        return this.#connection.state;
    }
    get connected() {
        return this.#connection.state === "connected";
    }
    get snapshot() {
        return this.#state.snapshot;
    }
    static async connect(options) {
        const client = new PiClient(options);
        try {
            await client.connect();
            return client;
        }
        catch (error) {
            await client.dispose();
            throw error;
        }
    }
    connect() {
        if (this.#disposed)
            return Promise.reject(new PiClientDisposedError());
        if (this.#connection.state === "disconnected")
            this.#state.reset();
        return this.#connection.connect();
    }
    reconnect() {
        return this.connect();
    }
    disconnect(reason = "Client disconnected") {
        this.#connection.disconnect(reason);
    }
    subscribe(listener) {
        this.#assertNotDisposed();
        return this.#state.subscribe(listener);
    }
    onEvent(listener) {
        this.#assertNotDisposed();
        return this.#state.onEvent(listener);
    }
    onConnectionStateChange(listener) {
        this.#assertNotDisposed();
        this.#connectionStateListeners.add(listener);
        return () => this.#connectionStateListeners.delete(listener);
    }
    async listSessions() {
        return (await this.#request({ command: "list" })).sessions;
    }
    async createSession(options = {}) {
        const result = await this.#request({ command: "create", ...options });
        const token = this.#reserveSessionLease(result.session.id, "exclusive");
        return this.#createSessionLease(result.session.id, token);
    }
    async attachSession(sessionId) {
        return this.acquireSession(sessionId, { mode: "shared" });
    }
    async acquireSession(sessionId, options) {
        this.#assertNotDisposed();
        const token = this.#reserveSessionLease(sessionId, options.mode);
        try {
            const detachment = this.#sessionDetachments.get(sessionId);
            if (detachment)
                await detachment.catch(() => { });
            const reconciled = this.#sessionCleanupRequired.has(sessionId)
                ? await this.#reconcileSessionCleanup(sessionId)
                : false;
            if (reconciled || !this.#state.isSessionAttached(sessionId)) {
                let attachment = this.#sessionAttachments.get(sessionId);
                if (!attachment) {
                    attachment = this.#attachSession(sessionId);
                    this.#sessionAttachments.set(sessionId, attachment);
                }
                try {
                    await attachment;
                }
                finally {
                    if (this.#sessionAttachments.get(sessionId) === attachment)
                        this.#sessionAttachments.delete(sessionId);
                }
            }
            return this.#createSessionLease(sessionId, token);
        }
        catch (error) {
            this.#releaseSessionLease(sessionId, token);
            throw error;
        }
    }
    async #attachSession(sessionId) {
        const previous = this.#state.forgetSessionSnapshot(sessionId);
        try {
            await this.#request({ command: "attach", sessionId });
        }
        catch (error) {
            if (previous)
                this.#state.restoreSessionSnapshot(previous);
            throw error;
        }
    }
    #request(command) {
        if (this.#disposed)
            return Promise.reject(new PiClientDisposedError());
        if (!this.connected)
            return Promise.reject(new PiDisconnectedError());
        const id = `request-${++this.#requestSequence}`;
        const { promise, resolve, reject } = createPromiseResolvers();
        this.#pendingRequests.set(id, { command, resolve, reject });
        let frame;
        try {
            frame = encodeClientMessage({ type: "request", id, request: command }, { maxFrameLength: this.#connection.maxFrameLength });
        }
        catch (error) {
            this.#takePendingRequest(id)?.reject(toError(error));
            return promise;
        }
        this.#connection.send(frame);
        return promise;
    }
    #createSessionLease(sessionId, token) {
        const generation = this.#sessionLeaseGenerations.get(sessionId) ?? 0;
        this.#sessionLeaseGenerations.set(sessionId, generation);
        let state = "active";
        let releasePromise;
        const refreshState = () => {
            if ((state === "active" || state === "releasing") &&
                this.#sessionLeaseGenerations.get(sessionId) !== generation) {
                state = "invalidated";
            }
        };
        const isActive = () => {
            refreshState();
            return state === "active" && this.#state.isSessionAttached(sessionId);
        };
        const assertActive = () => {
            this.#assertNotDisposed();
            if (!this.connected)
                throw new PiDisconnectedError();
            if (!isActive())
                throw new PiSessionDetachedError(sessionId);
        };
        const release = (relinquishOnFailure) => {
            refreshState();
            if (state === "released" || state === "invalidated")
                return Promise.resolve();
            if (releasePromise)
                return releasePromise;
            assertActive();
            state = "releasing";
            releasePromise = (async () => {
                const count = this.#sessionLeaseCounts.get(sessionId) ?? 0;
                if (count <= 1) {
                    const detachment = this.#request({ command: "detach", sessionId }).then(() => undefined);
                    this.#sessionDetachments.set(sessionId, detachment);
                    try {
                        await detachment;
                        this.#releaseSessionLease(sessionId, token);
                    }
                    finally {
                        if (this.#sessionDetachments.get(sessionId) === detachment) {
                            this.#sessionDetachments.delete(sessionId);
                        }
                    }
                }
                else {
                    this.#releaseSessionLease(sessionId, token);
                }
                state = "released";
            })().catch((error) => {
                refreshState();
                if (state === "invalidated")
                    return;
                if (relinquishOnFailure) {
                    this.#releaseSessionLease(sessionId, token);
                    this.#sessionCleanupRequired.add(sessionId);
                    state = "released";
                }
                else {
                    state = "active";
                    releasePromise = undefined;
                }
                throw error;
            });
            return releasePromise;
        };
        const callbacks = {
            isAttached: isActive,
            getSnapshot: () => (isActive() ? this.#state.getSessionSnapshot(sessionId) : undefined),
            subscribe: (listener) => {
                assertActive();
                return this.#state.subscribeSession(sessionId, (snapshot) => {
                    if (isActive())
                        listener(snapshot);
                });
            },
            onEvent: (listener) => {
                assertActive();
                return this.#state.onSessionEvent(sessionId, (event) => {
                    if (isActive() || event.type === "session_removed")
                        listener(event);
                });
            },
            detach: () => release(false),
            dispose: () => release(true),
            request: (command) => {
                assertActive();
                return this.#request(command);
            },
        };
        return new SessionHandle(sessionId, callbacks);
    }
    #handleMessage(message) {
        if (message.type === "event") {
            if (message.event.type === "session_removed")
                this.#invalidateSessionLeases(message.event.sessionId);
            this.#state.applyEvent(message.event);
            return;
        }
        const pending = this.#takePendingRequest(message.id);
        if (!pending) {
            this.#connection.fail(new ProtocolValidationError("Response has no matching request"));
            return;
        }
        if (!message.ok) {
            pending.reject(new PiServerError(message.error));
            return;
        }
        if (message.result.command !== pending.command.command) {
            const error = new ProtocolValidationError(`Response command ${message.result.command} does not match ${pending.command.command}`);
            pending.reject(error);
            this.#connection.fail(error);
            return;
        }
        this.#state.applyResult(message.result);
        pending.resolve(message.result);
    }
    #handleConnectionStateChange(change) {
        if (change.state === "disconnected") {
            this.#state.clearAttachments();
            this.#invalidateAllSessionLeases();
            this.#rejectPendingRequests(change.error ?? new PiDisconnectedError());
        }
        this.#notifyConnectionStateListeners(change);
    }
    #takePendingRequest(id) {
        const request = this.#pendingRequests.get(id);
        if (request)
            this.#pendingRequests.delete(id);
        return request;
    }
    #rejectPendingRequests(error) {
        const requests = [...this.#pendingRequests.values()];
        this.#pendingRequests.clear();
        for (const request of requests)
            request.reject(error);
    }
    dispose() {
        if (this.#disposePromise)
            return this.#disposePromise;
        this.#disposed = true;
        this.#disposePromise = Promise.resolve();
        const error = new PiClientDisposedError();
        this.#rejectPendingRequests(error);
        this.#connection.disconnect(error);
        this.#state.dispose();
        this.#invalidateAllSessionLeases();
        this.#connectionStateListeners.clear();
        return this.#disposePromise;
    }
    [Symbol.asyncDispose]() {
        return this.dispose();
    }
    #assertNotDisposed() {
        if (this.#disposed)
            throw new PiClientDisposedError();
    }
    async #reconcileSessionCleanup(sessionId) {
        if (!this.#sessionCleanupRequired.has(sessionId))
            return false;
        let reconciliation = this.#sessionReconciliations.get(sessionId);
        if (!reconciliation) {
            reconciliation = this.#request({ command: "detach", sessionId })
                .then(() => undefined)
                .then(() => {
                this.#sessionCleanupRequired.delete(sessionId);
            })
                .finally(() => {
                this.#sessionReconciliations.delete(sessionId);
            });
            this.#sessionReconciliations.set(sessionId, reconciliation);
        }
        await reconciliation;
        return true;
    }
    #reserveSessionLease(sessionId, mode) {
        const count = this.#sessionLeaseCounts.get(sessionId) ?? 0;
        if (mode === "exclusive" && count > 0) {
            throw new PiSessionOwnershipError(sessionId, `Session ${sessionId} already has an active lease`);
        }
        if (mode === "shared" && this.#exclusiveSessionLeases.has(sessionId)) {
            throw new PiSessionOwnershipError(sessionId, `Session ${sessionId} has an exclusive lease`);
        }
        const token = { mode };
        this.#sessionLeaseCounts.set(sessionId, count + 1);
        if (mode === "exclusive")
            this.#exclusiveSessionLeases.set(sessionId, token);
        return token;
    }
    #releaseSessionLease(sessionId, token) {
        const count = this.#sessionLeaseCounts.get(sessionId) ?? 0;
        if (count <= 1)
            this.#sessionLeaseCounts.delete(sessionId);
        else
            this.#sessionLeaseCounts.set(sessionId, count - 1);
        if (this.#exclusiveSessionLeases.get(sessionId) === token)
            this.#exclusiveSessionLeases.delete(sessionId);
    }
    #invalidateSessionLeases(sessionId) {
        this.#sessionLeaseCounts.delete(sessionId);
        this.#exclusiveSessionLeases.delete(sessionId);
        this.#sessionCleanupRequired.delete(sessionId);
        this.#sessionLeaseGenerations.set(sessionId, (this.#sessionLeaseGenerations.get(sessionId) ?? 0) + 1);
    }
    #invalidateAllSessionLeases() {
        for (const sessionId of this.#sessionLeaseCounts.keys())
            this.#invalidateSessionLeases(sessionId);
        this.#sessionCleanupRequired.clear();
    }
    #notifyConnectionStateListeners(change) {
        for (const listener of this.#connectionStateListeners) {
            try {
                listener(change);
            }
            catch (error) {
                this.#reportListenerError(error);
            }
        }
    }
    #reportListenerError(error) {
        if (!this.#options.onListenerError)
            return;
        try {
            this.#options.onListenerError(toError(error));
        }
        catch {
            // Diagnostics cannot affect protocol or transport state.
        }
    }
}
//# sourceMappingURL=client.js.map
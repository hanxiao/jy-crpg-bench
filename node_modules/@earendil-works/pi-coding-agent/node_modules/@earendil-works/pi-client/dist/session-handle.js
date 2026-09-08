export class SessionHandle {
    id;
    #callbacks;
    constructor(id, callbacks) {
        this.id = id;
        this.#callbacks = callbacks;
    }
    get attached() {
        return this.#callbacks.isAttached();
    }
    get active() {
        return this.attached;
    }
    get snapshot() {
        return this.#callbacks.getSnapshot();
    }
    subscribe(listener) {
        return this.#callbacks.subscribe(listener);
    }
    onEvent(listener) {
        return this.#callbacks.onEvent(listener);
    }
    async detach() {
        await this.#callbacks.detach();
    }
    dispose() {
        return this.#callbacks.dispose();
    }
    [Symbol.asyncDispose]() {
        return this.dispose();
    }
    async prompt(text) {
        return (await this.#request({ command: "prompt", sessionId: this.id, text })).session;
    }
    async steer(text) {
        return (await this.#request({ command: "steer", sessionId: this.id, text })).session;
    }
    async abort() {
        return (await this.#request({ command: "abort", sessionId: this.id })).session;
    }
    async setModel(model) {
        return (await this.#request({ command: "set_model", sessionId: this.id, model })).session;
    }
    async setThinking(thinkingLevel) {
        return (await this.#request({ command: "set_thinking", sessionId: this.id, thinkingLevel })).session;
    }
    #request(command) {
        return this.#callbacks.request(command);
    }
}
//# sourceMappingURL=session-handle.js.map
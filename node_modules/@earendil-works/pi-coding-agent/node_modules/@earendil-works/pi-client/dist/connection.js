import { DEFAULT_MAX_FRAME_LENGTH, encodeClientMessage, PROTOCOL_VERSION, ProtocolValidationError, ServerMessageDecoder, } from "@earendil-works/pi-protocol";
import { PiDisconnectedError, PiServerError, toDisconnectedError, toError } from "./errors.js";
import { createPromiseResolvers } from "./promise.js";
const MAX_UINT32 = 0xffff_ffff;
export class Connection {
    #options;
    #maxFrameLength;
    #lifecycle = { state: "disconnected" };
    #sequence = 0;
    constructor(options) {
        this.#options = options;
        this.#maxFrameLength = options.maxFrameLength ?? DEFAULT_MAX_FRAME_LENGTH;
        if (!Number.isSafeInteger(this.#maxFrameLength) ||
            this.#maxFrameLength <= 0 ||
            this.#maxFrameLength > MAX_UINT32) {
            throw new TypeError(`PiClient maxFrameLength must be an integer between 1 and ${MAX_UINT32}`);
        }
    }
    get state() {
        return this.#lifecycle.state;
    }
    get maxFrameLength() {
        return this.#maxFrameLength;
    }
    connect() {
        if (this.#lifecycle.state !== "disconnected") {
            return Promise.reject(new PiDisconnectedError(`PiClient is already ${this.#lifecycle.state}`));
        }
        const id = ++this.#sequence;
        const handshake = createPromiseResolvers();
        this.#lifecycle = {
            state: "connecting",
            id,
            decoder: new ServerMessageDecoder({ maxFrameLength: this.#maxFrameLength }),
            handshake,
        };
        this.#options.onStateChange({ state: "connecting" });
        const handlers = {
            onData: (chunk) => this.#handleData(id, chunk),
            onClose: () => {
                if (this.#isCurrent(id))
                    this.#handleClose();
            },
            onError: (error) => {
                if (this.#isCurrent(id))
                    this.#failAndClose(toDisconnectedError(error));
            },
        };
        void this.#openTransport(id, handlers);
        return handshake.promise;
    }
    disconnect(reason = "Client disconnected") {
        if (this.#lifecycle.state === "disconnected")
            return;
        this.#failAndClose(typeof reason === "string" ? new PiDisconnectedError(reason) : reason);
    }
    fail(error) {
        this.#failAndClose(error);
    }
    send(frame) {
        const lifecycle = this.#lifecycle;
        if (lifecycle.state !== "connected")
            throw new PiDisconnectedError();
        let sending;
        try {
            sending = lifecycle.transport.send(frame);
        }
        catch (error) {
            this.#failAndClose(toDisconnectedError(error));
            return;
        }
        void sending.catch((error) => {
            const current = this.#lifecycle;
            if (current.state !== "disconnected" && current.transport === lifecycle.transport) {
                this.#failAndClose(toDisconnectedError(error));
            }
        });
    }
    async #openTransport(id, handlers) {
        let transport;
        try {
            transport = await this.#options.transportFactory(handlers);
        }
        catch (error) {
            if (this.#isCurrent(id))
                this.#fail(toDisconnectedError(error));
            return;
        }
        const lifecycle = this.#lifecycle;
        if (lifecycle.state !== "connecting" || lifecycle.id !== id) {
            transport.close();
            return;
        }
        this.#lifecycle = { ...lifecycle, transport };
        try {
            await transport.send(encodeClientMessage({ type: "hello", version: PROTOCOL_VERSION }, { maxFrameLength: this.#maxFrameLength }));
        }
        catch (error) {
            if (this.#isCurrent(id))
                this.#failAndClose(toDisconnectedError(error));
        }
    }
    #handleData(id, chunk) {
        const lifecycle = this.#lifecycle;
        if (lifecycle.state === "disconnected" || lifecycle.id !== id)
            return;
        if (lifecycle.state === "connecting" && !lifecycle.transport) {
            this.#failAndClose(new ProtocolValidationError("Received server data before the client hello was sent"));
            return;
        }
        let messages;
        try {
            messages = lifecycle.decoder.push(chunk);
        }
        catch (error) {
            this.#failAndClose(toError(error));
            return;
        }
        for (const message of messages) {
            if (this.#lifecycle.state === "disconnected")
                return;
            this.#handleMessage(message);
        }
    }
    #handleMessage(message) {
        const lifecycle = this.#lifecycle;
        if (lifecycle.state === "connecting") {
            if (message.type === "hello_error") {
                this.#failAndClose(new PiServerError(message.error));
                return;
            }
            if (message.type !== "hello") {
                this.#failAndClose(new ProtocolValidationError("Expected server hello as first message"));
                return;
            }
            if (!lifecycle.transport) {
                this.#failAndClose(new ProtocolValidationError("Received server hello before the client hello was sent"));
                return;
            }
            const connected = {
                state: "connected",
                id: lifecycle.id,
                decoder: lifecycle.decoder,
                transport: lifecycle.transport,
                handshake: lifecycle.handshake,
            };
            this.#lifecycle = connected;
            try {
                this.#options.onHandshake(message.snapshot);
            }
            catch (error) {
                if (this.#lifecycle === connected)
                    this.#failAndClose(toError(error));
                return;
            }
            if (this.#lifecycle !== connected)
                return;
            this.#options.onStateChange({ state: "connected" });
            if (this.#lifecycle !== connected)
                return;
            this.#lifecycle = { ...connected, handshake: undefined };
            lifecycle.handshake.resolve(message.snapshot);
            return;
        }
        if (lifecycle.state !== "connected")
            return;
        if (message.type === "hello" || message.type === "hello_error") {
            this.#failAndClose(new ProtocolValidationError("Unexpected handshake message"));
            return;
        }
        this.#options.onMessage(message);
    }
    #handleClose() {
        const lifecycle = this.#lifecycle;
        if (lifecycle.state === "disconnected")
            return;
        let error = new PiDisconnectedError("Byte transport closed");
        try {
            lifecycle.decoder.end();
        }
        catch (decoderError) {
            error = toError(decoderError);
        }
        this.#fail(error);
    }
    #failAndClose(error) {
        const lifecycle = this.#lifecycle;
        const transport = lifecycle.state === "disconnected" ? undefined : lifecycle.transport;
        this.#fail(error);
        transport?.close();
    }
    #fail(error) {
        const lifecycle = this.#lifecycle;
        if (lifecycle.state === "disconnected")
            return;
        this.#lifecycle = { state: "disconnected" };
        lifecycle.handshake?.reject(error);
        this.#options.onStateChange({ state: "disconnected", error });
    }
    #isCurrent(id) {
        return this.#lifecycle.state !== "disconnected" && this.#lifecycle.id === id;
    }
}
//# sourceMappingURL=connection.js.map
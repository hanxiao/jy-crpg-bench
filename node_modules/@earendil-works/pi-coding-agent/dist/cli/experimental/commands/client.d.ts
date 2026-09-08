import type { AuthInput } from "../auth.ts";
import { Command } from "../command.ts";
import type { TransportAddress } from "../transport-address.ts";
export interface ClientCommand {
    readonly command: "client";
    readonly auth?: AuthInput;
    readonly connect?: TransportAddress;
}
export interface ClientCommandContext {
    runClient(command: ClientCommand): void | Promise<void>;
}
export declare const clientCommand: Command<ClientCommand, ClientCommandContext, ClientCommand>;
//# sourceMappingURL=client.d.ts.map
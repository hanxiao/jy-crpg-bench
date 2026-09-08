import type { AuthInput } from "../auth.ts";
import { Command } from "../command.ts";
import type { TransportAddress } from "../transport-address.ts";
export interface ServerCommand {
    readonly command: "server";
    readonly auth?: AuthInput;
    readonly listen?: readonly TransportAddress[];
}
export interface ServerCommandContext {
    runServer(command: ServerCommand): void | Promise<void>;
}
export declare const serverCommand: Command<ServerCommand, ServerCommandContext, ServerCommand>;
//# sourceMappingURL=server.d.ts.map
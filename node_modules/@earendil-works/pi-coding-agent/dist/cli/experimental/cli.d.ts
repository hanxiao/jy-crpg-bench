import { type ClientCommandContext } from "./commands/client.ts";
import { type PiCommandContext } from "./commands/pi.ts";
import { type ServerCommandContext } from "./commands/server.ts";
export type ExperimentalCliContext = PiCommandContext & ServerCommandContext & ClientCommandContext;
export declare const experimentalCli: import("./command.ts").Command<import("./commands/pi.ts").PiCommand, PiCommandContext & ServerCommandContext & ClientCommandContext, import("./commands/client.ts").ClientCommand | import("./commands/pi.ts").PiCommand | import("./commands/server.ts").ServerCommand>;
//# sourceMappingURL=cli.d.ts.map
import type { Args } from "../../args.ts";
import type { AuthInput } from "../auth.ts";
import { Command } from "../command.ts";
import type { TransportAddress } from "../transport-address.ts";
export interface PiCommand {
    readonly command: "pi";
    readonly auth?: AuthInput;
    readonly options: Args;
    readonly listen?: readonly TransportAddress[];
}
export interface PiCommandContext {
    runPi(command: PiCommand): void | Promise<void>;
}
export declare const piCommand: Command<PiCommand, PiCommandContext, PiCommand>;
//# sourceMappingURL=pi.d.ts.map
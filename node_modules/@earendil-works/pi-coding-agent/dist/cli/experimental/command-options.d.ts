import { type Args } from "../args.ts";
import { type AuthInput } from "./auth.ts";
import { type CommandOption, type ParsedCommandInput } from "./command.ts";
import { type TransportAddress } from "./transport-address.ts";
export declare const authTokenOption: CommandOption<string>;
export declare const authTokenFileOption: CommandOption<string>;
export declare function transportOption(name: "--listen" | "--connect"): CommandOption<TransportAddress>;
export declare function parseAuth(input: ParsedCommandInput): {
    auth?: AuthInput;
    errors: string[];
};
export declare function parseLegacyOptions(input: ParsedCommandInput): {
    options: Args;
    errors: string[];
};
export declare function unsupportedLegacyOptions(command: string, input: ParsedCommandInput): string[];
//# sourceMappingURL=command-options.d.ts.map
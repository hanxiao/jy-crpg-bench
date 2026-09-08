import { Command } from "../command.js";
import { authTokenFileOption, authTokenOption, parseAuth, parseLegacyOptions, transportOption, unsupportedLegacyOptions, } from "../command-options.js";
const connectOption = transportOption("--connect");
export const clientCommand = new Command("client")
    .option(connectOption)
    .option(authTokenOption)
    .option(authTokenFileOption)
    .build((input) => {
    const { auth, errors: authErrors } = parseAuth(input);
    const connect = input.value(connectOption);
    const { errors: optionErrors } = parseLegacyOptions(input);
    const errors = [...authErrors, ...optionErrors, ...unsupportedLegacyOptions("client", input)];
    if (errors.length > 0)
        return { ok: false, errors };
    return {
        ok: true,
        command: {
            command: "client",
            ...(auth === undefined ? {} : { auth }),
            ...(connect === undefined ? {} : { connect }),
        },
    };
})
    .action((command, context) => context.runClient(command));
//# sourceMappingURL=client.js.map
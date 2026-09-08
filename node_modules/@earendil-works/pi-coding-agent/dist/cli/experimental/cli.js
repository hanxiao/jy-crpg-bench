import { clientCommand } from "./commands/client.js";
import { piCommand } from "./commands/pi.js";
import { serverCommand } from "./commands/server.js";
export const experimentalCli = piCommand.command(serverCommand).command(clientCommand);
//# sourceMappingURL=cli.js.map
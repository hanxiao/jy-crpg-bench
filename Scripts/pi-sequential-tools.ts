// Run the tool calls of one assistant message one after another.
//
// pi runs the tool calls of one assistant message in parallel. A model that
// presses keys with bash and reads the screenshot with read in the same
// message then reads the file before the keys are sent, so it sees the screen
// from before its own action. In batch 20261010-120518, 321 to 409 of the
// screenshots in each Claude run that did this were read before the key press
// they were sent with had finished.
//
// The four tools are registered again exactly as pi builds them, with pi's own
// settings, and marked sequential. One sequential tool in a message makes pi
// run every call of that message in order, so a read after a bash sees what
// the bash wrote.
//
//   pi -e Scripts/pi-sequential-tools.ts ...

import {
  createBashToolDefinition,
  createEditToolDefinition,
  createReadToolDefinition,
  createWriteToolDefinition,
} from "@earendil-works/pi-coding-agent";

export default function (pi: any) {
  // Settings can be read only once the session has started.
  pi.on("session_start", async (_event: any, ctx: any) => {
    const cwd = ctx?.cwd ?? process.cwd();
    const settings = pi.getSettings() ?? {};
    const tools = [
      createReadToolDefinition(cwd, { autoResizeImages: settings.images?.autoResize ?? true }),
      createBashToolDefinition(cwd, {
        commandPrefix: settings.shellCommandPrefix,
        shellPath: settings.shellPath,
      }),
      createEditToolDefinition(cwd),
      createWriteToolDefinition(cwd),
    ];
    for (const tool of tools) pi.registerTool({ ...tool, executionMode: "sequential" });
  });
}

import { AgentHarness, type AgentHarnessOptions, type ExecutionEnv, type HarnessTool } from "@earendil-works/pi-agent-core";
import { type BuildSystemPromptOptions } from "../core/system-prompt.ts";
export interface CodingAgentHarnessTool extends HarnessTool {
    promptSnippet?: string;
    promptGuidelines?: readonly string[];
}
export interface CreateCodingAgentHarnessOptions extends Omit<AgentHarnessOptions, "toolContext" | "tools"> {
    env: ExecutionEnv;
    bashCommandPrefix?: string;
    /** Path to the JSONL session file exposed to default bash commands as PI_SESSION_FILE. */
    sessionFile?: string;
    tools?: CodingAgentHarnessTool[];
    systemPromptOptions?: Omit<BuildSystemPromptOptions, "cwd" | "promptGuidelines" | "selectedTools" | "toolSnippets">;
}
export interface BuildCodingAgentHarnessSystemPromptOptions {
    cwd: string;
    tools: readonly CodingAgentHarnessTool[];
    activeToolNames: readonly string[];
    systemPromptOptions?: CreateCodingAgentHarnessOptions["systemPromptOptions"];
}
export declare function buildCodingAgentHarnessSystemPrompt(options: BuildCodingAgentHarnessSystemPromptOptions): string;
export declare function createCodingAgentHarness(options: CreateCodingAgentHarnessOptions): Promise<{
    harness: AgentHarness;
    suspended: import("@earendil-works/pi-agent-core").SuspendedOperation[];
}>;
//# sourceMappingURL=create-harness.d.ts.map
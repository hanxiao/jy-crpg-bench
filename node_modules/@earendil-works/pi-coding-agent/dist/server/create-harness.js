import { AgentHarness, createBashTool, createEditTool, createReadTool, createWriteTool, } from "@earendil-works/pi-agent-core";
import { getExperimentalToolSampling } from "../core/experimental.js";
import { buildSystemPrompt } from "../core/system-prompt.js";
import { bashToolSystemPromptContribution } from "../core/tools/bash.js";
import { editToolSystemPromptContribution } from "../core/tools/edit.js";
import { readToolSystemPromptContribution } from "../core/tools/read.js";
import { writeToolSystemPromptContribution } from "../core/tools/write.js";
function createCodingAgentHarnessTool(tool, context, prompt) {
    return {
        ...tool,
        ...prompt,
        constrainedSampling: getExperimentalToolSampling(),
        execute: (toolCallId, params, signal, onUpdate) => tool.execute(toolCallId, params, signal, onUpdate, context),
    };
}
export function buildCodingAgentHarnessSystemPrompt(options) {
    const activeTools = options.activeToolNames.flatMap((name) => {
        const tool = options.tools.find((candidate) => candidate.name === name);
        return tool ? [tool] : [];
    });
    const toolSnippets = Object.fromEntries(activeTools.flatMap((tool) => {
        const promptSnippet = tool.promptSnippet
            ?.replace(/[\r\n]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();
        return promptSnippet ? [[tool.name, promptSnippet]] : [];
    }));
    const promptGuidelines = activeTools.flatMap((tool) => tool.promptGuidelines ?? []);
    return buildSystemPrompt({
        ...options.systemPromptOptions,
        cwd: options.cwd,
        selectedTools: activeTools.map((tool) => tool.name),
        toolSnippets,
        promptGuidelines,
    });
}
export async function createCodingAgentHarness(options) {
    const { env, bashCommandPrefix, sessionFile, systemPromptOptions, tools: providedTools, activeToolNames: providedActiveToolNames, systemPrompt: providedSystemPrompt, ...harnessOptions } = options;
    let harness;
    const getHarness = () => {
        if (!harness)
            throw new Error("Coding-agent Harness callback ran before Harness initialization");
        return harness;
    };
    let tools = providedTools;
    if (tools === undefined) {
        const metadata = await options.session.getMetadata();
        const toolContext = { env };
        tools = [
            createCodingAgentHarnessTool(createReadTool(), toolContext, {
                promptSnippet: readToolSystemPromptContribution.snippet,
                promptGuidelines: readToolSystemPromptContribution.guidelines,
            }),
            createCodingAgentHarnessTool(createBashTool({
                commandPrefix: bashCommandPrefix,
                prepare: async (execution) => {
                    const currentHarness = getHarness();
                    const [model, thinkingLevel] = await Promise.all([
                        currentHarness.getModel(),
                        currentHarness.getThinkingLevel(),
                    ]);
                    execution.env.PI_SESSION_ID = metadata.id;
                    execution.env.PI_SESSION_FILE = sessionFile ?? "";
                    execution.env.PI_PROVIDER = model.provider;
                    execution.env.PI_MODEL = model.id;
                    execution.env.PI_REASONING_LEVEL = thinkingLevel;
                },
            }), toolContext, {
                promptSnippet: bashToolSystemPromptContribution.snippet,
                promptGuidelines: bashToolSystemPromptContribution.guidelines,
            }),
            createCodingAgentHarnessTool(createEditTool(), toolContext, {
                promptSnippet: editToolSystemPromptContribution.snippet,
                promptGuidelines: editToolSystemPromptContribution.guidelines,
            }),
            createCodingAgentHarnessTool(createWriteTool(), toolContext, {
                promptSnippet: writeToolSystemPromptContribution.snippet,
                promptGuidelines: writeToolSystemPromptContribution.guidelines,
            }),
        ];
    }
    const activeToolNames = [...(providedActiveToolNames ?? tools.map((tool) => tool.name))];
    const systemPrompt = providedSystemPrompt ??
        (async () => {
            const currentHarness = getHarness();
            const [currentTools, currentActiveToolNames] = await Promise.all([
                currentHarness.getTools(),
                currentHarness.getActiveTools(),
            ]);
            return buildCodingAgentHarnessSystemPrompt({
                cwd: env.cwd,
                tools: currentTools,
                activeToolNames: currentActiveToolNames,
                systemPromptOptions,
            });
        });
    const created = await AgentHarness.create({
        ...harnessOptions,
        tools,
        activeToolNames,
        systemPrompt,
    });
    harness = created.harness;
    return created;
}
//# sourceMappingURL=create-harness.js.map
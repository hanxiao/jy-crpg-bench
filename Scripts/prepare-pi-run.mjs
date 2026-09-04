#!/usr/bin/env node
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

const required = [
  "QUNXIA_ROOT",
  "QUNXIA_RUN_DIR",
  "QUNXIA_RUN_ID",
  "QUNXIA_PI_PROFILE",
  "QUNXIA_PI_VERSION",
  "QUNXIA_LLM_BASE_URL",
  "QUNXIA_MODEL_REF",
  "QUNXIA_API",
];

for (const name of required) {
  if (!process.env[name]) throw new Error(`${name} is required`);
}

const root = process.env.QUNXIA_ROOT;
const runDir = process.env.QUNXIA_RUN_DIR;
const runId = process.env.QUNXIA_RUN_ID;
const profile = process.env.QUNXIA_PI_PROFILE;
const resume = process.env.QUNXIA_RESUME === "1";
const modelRef = process.env.QUNXIA_MODEL_REF;
const slash = modelRef.indexOf("/");
if (slash <= 0 || slash === modelRef.length - 1) {
  throw new Error("QUNXIA_MODEL_REF must contain provider/model");
}
const modelProvider = modelRef.slice(0, slash);
const modelId = modelRef.slice(slash + 1);
const configDir = join(runDir, "config");
const sessionDir = join(runDir, "sessions");
const workspaceDir = join(runDir, "workspace");
const manifestPath = join(runDir, "run.json");
let existingManifest = null;
if (resume) {
  try {
    existingManifest = JSON.parse(await readFile(manifestPath, "utf8"));
  } catch (error) {
    throw new Error(`cannot resume ${runId}: ${error.message}`);
  }
}

const profileFile = join(root, "pi-agent", "profiles.json");
const profiles = JSON.parse(await readFile(profileFile, "utf8"));
const profileDefinition = profiles[profile];
if (!profileDefinition) {
  throw new Error(
    `unknown QUNXIA_PI_PROFILE ${profile}; available profiles: ${Object.keys(profiles).join(", ")}`,
  );
}
if (!["standalone", "session-help"].includes(profileDefinition.prompt)) {
  throw new Error(`profile ${profile} has an invalid prompt source`);
}
if (!Number.isInteger(profileDefinition.scale) || profileDefinition.scale !== 1) {
  throw new Error(`profile ${profile} must use the native observation scale`);
}
if (typeof profileDefinition.observeAfterAction !== "boolean") {
  throw new Error(`profile ${profile} must declare observeAfterAction`);
}

const extensionTools = {
  qunxia: [
    "game_look",
    "game_press",
    "game_press_sequence",
    "game_move",
    "game_wait",
    "game_save",
    "game_load",
    "game_saves",
  ],
};
if (!Array.isArray(profileDefinition.extensions) || !profileDefinition.extensions.includes("qunxia")) {
  throw new Error(`profile ${profile} must load the qunxia extension`);
}
if (profileDefinition.extensions.some((name) => !(name in extensionTools))) {
  throw new Error(`profile ${profile} contains an unknown extension`);
}
const allowedTools = new Set(profileDefinition.extensions.flatMap((name) => extensionTools[name]));
if (!Array.isArray(profileDefinition.tools) || profileDefinition.tools.length === 0) {
  throw new Error(`profile ${profile} must declare at least one tool`);
}
if (profileDefinition.tools.some((name) => !allowedTools.has(name))) {
  throw new Error(`profile ${profile} contains a tool not supplied by its isolated extensions`);
}
if (new Set(profileDefinition.tools).size !== profileDefinition.tools.length) {
  throw new Error(`profile ${profile} contains duplicate tools`);
}

// This is an explicit model definition, not a shared Pi account/configuration.
// Resume defaults to the definition snapshotted in the run manifest.
const modelDefinition = process.env.QUNXIA_MODEL_CONFIG
  ? JSON.parse(await readFile(process.env.QUNXIA_MODEL_CONFIG, "utf8"))
  : (existingManifest?.model ?? {});
if (process.env.QUNXIA_MODEL_CONFIG && modelDefinition.id !== modelId) {
  throw new Error("model definition id does not match the requested provider/model");
}
let input;
try {
  input = process.env.QUNXIA_LLM_INPUT_JSON
    ? JSON.parse(process.env.QUNXIA_LLM_INPUT_JSON)
    : (modelDefinition.input ?? ["text", "image"]);
} catch (error) {
  throw new Error(`QUNXIA_LLM_INPUT must be a JSON array: ${error.message}`);
}
if (
  !Array.isArray(input) ||
  input.length === 0 ||
  new Set(input).size !== input.length ||
  input.some((item) => !["text", "image"].includes(item))
) {
  throw new Error('QUNXIA_LLM_INPUT must contain only "text" and "image"');
}

const contextWindow = Number(process.env.QUNXIA_LLM_CONTEXT || modelDefinition.contextWindow || 128000);
if (!Number.isSafeInteger(contextWindow) || contextWindow <= 0) {
  throw new Error("QUNXIA_LLM_CONTEXT must be a positive integer");
}
const maxTokens = Number(process.env.QUNXIA_LLM_MAX_TOKENS || modelDefinition.maxTokens || 8192);
if (!Number.isSafeInteger(maxTokens) || maxTokens <= 0 || maxTokens > contextWindow) {
  throw new Error("QUNXIA_LLM_MAX_TOKENS must be a positive integer no larger than QUNXIA_LLM_CONTEXT");
}
const api = process.env.QUNXIA_LLM_API || modelDefinition.api || "openai-completions";
if (!["openai-completions", "openai-responses", "google-generative-ai"].includes(api)) {
  throw new Error("QUNXIA_LLM_API must be openai-completions, openai-responses or google-generative-ai");
}
const parseFlag = (name, fallback) => {
  const value = process.env[name];
  if (!value) return fallback;
  if (value !== "0" && value !== "1") throw new Error(`${name} must be 0 or 1`);
  return value === "1";
};
const reasoning = parseFlag("QUNXIA_LLM_REASONING", modelDefinition.reasoning === true);
const supportsReasoningEffort = parseFlag(
  "QUNXIA_LLM_SUPPORTS_REASONING_EFFORT", modelDefinition.supportsReasoningEffort === true);
const requestedThinking = process.env.QUNXIA_THINKING || null;
let thinkingLevel = resume && requestedThinking === null
  ? (existingManifest?.model?.thinkingLevel ?? null)
  : requestedThinking;
const thinkingLevels = new Set(["off", "minimal", "low", "medium", "high", "xhigh", "max"]);
if (thinkingLevel !== null && !thinkingLevels.has(thinkingLevel)) {
  throw new Error("QUNXIA_THINKING has an invalid level");
}
if (profile === "benchmark" && thinkingLevel === null) {
  throw new Error("benchmark runs require an explicit QUNXIA_THINKING level");
}
const thinkingLevelMap = modelDefinition.thinkingLevelMap ?? {};
if (typeof thinkingLevelMap !== "object" || Array.isArray(thinkingLevelMap)
    || Object.entries(thinkingLevelMap).some(([level, value]) =>
      !thinkingLevels.has(level) || (value !== null && (typeof value !== "string" || !value)))) {
  throw new Error("thinkingLevelMap must map Pi levels to provider strings or null");
}
// Match Pi's supported-level contract: extended levels require model metadata;
// requesting max must never manufacture max support for an arbitrary model.
const supportedThinkingLevels = [...thinkingLevels].filter(level => reasoning
  ? thinkingLevelMap[level] !== null && (!["xhigh", "max"].includes(level)
      || typeof thinkingLevelMap[level] === "string")
  : level === "off");
thinkingLevel ??= supportedThinkingLevels.includes("medium") ? "medium" : supportedThinkingLevels[0];
if (thinkingLevel !== "off"
    && (!reasoning || (api === "openai-completions" && !supportsReasoningEffort))) {
  throw new Error(
    `QUNXIA_THINKING=${thinkingLevel} requires a reasoning model and an endpoint that supports reasoning effort`,
  );
}
if (!supportedThinkingLevels.includes(thinkingLevel)) {
  throw new Error(`unsupported thinking level ${thinkingLevel}; supported: ${supportedThinkingLevels.join(", ")}`);
}
// This is configuration metadata, not the adapter's final wire value. For
// example, Pi's Gemini adapter maps Pro medium to HIGH and handles off itself.
const mappedThinkingLevel = thinkingLevelMap[thinkingLevel] ?? (thinkingLevel === "off" ? null : thinkingLevel);
if (api === "google-generative-ai" && thinkingLevel !== "off"
    && !["minimal", "low", "medium", "high"].includes(mappedThinkingLevel.toLowerCase())) {
  throw new Error("Google thinkingLevelMap values must be minimal, low, medium or high");
}

let benchmarkHelp = null;
let systemPrompt;
let promptMetadata;
if (profileDefinition.prompt === "session-help") {
  const language = resume
    ? existingManifest?.prompt?.language
    : (process.env.QUNXIA_BENCH_LANG || "zh");
  const helpUrl = resume
    ? existingManifest?.prompt?.url
    : process.env.QUNXIA_BENCH_HELP_URL;

  if (resume) {
    try {
      benchmarkHelp = await readFile(join(configDir, "benchmark-help.md"), "utf8");
    } catch {
      throw new Error(`cannot resume ${runId}: benchmark help snapshot is missing`);
    }
  } else {
    if (!helpUrl) throw new Error(`profile ${profile} requires QUNXIA_BENCH_HELP_URL`);
    let response;
    try {
      response = await fetch(helpUrl, { signal: AbortSignal.timeout(30_000) });
    } catch (error) {
      throw new Error(`could not fetch benchmark help: ${error.message}`);
    }
    if (!response.ok) {
      throw new Error(`could not fetch benchmark help: HTTP ${response.status}`);
    }
    benchmarkHelp = await response.text();
  }

  const lines = benchmarkHelp.split("\n").map((line) => line.trim());
  const hasEndpoint = (method, path) => lines.some((line) => {
    const [seenMethod, url] = line.split(/\s+/, 2);
    return seenMethod === method && url?.endsWith(path);
  });
  const requirements = [
    ["GET /api/screen", hasEndpoint("GET", "/api/screen")],
    ["POST /api/key", hasEndpoint("POST", "/api/key")],
    ["POST /api/keys", hasEndpoint("POST", "/api/keys")],
    ["POST /api/wait", hasEndpoint("POST", "/api/wait")],
  ];
  const missing = requirements.filter(([, present]) => !present).map(([label]) => label);
  if (missing.length) {
    throw new Error(`benchmark help is incomplete; missing: ${missing.join(", ")}`);
  }

  const adapter = await readFile(join(root, "pi-agent", "BENCHMARK.md"), "utf8");
  systemPrompt = `${adapter}\n\n${benchmarkHelp}\n--- END SESSION-SPECIFIC BENCHMARK BRIEF ---\n`;
  promptMetadata = {
    source: "session-help",
    url: helpUrl,
    language,
    helpChars: benchmarkHelp.length,
  };
} else {
  systemPrompt = await readFile(join(root, "pi-agent", "SYSTEM.md"), "utf8");
  promptMetadata = { source: "pi-agent/SYSTEM.md" };
}

const identity = {
  runId,
  profile,
  piPackage: "@earendil-works/pi-coding-agent",
  piVersion: process.env.QUNXIA_PI_VERSION,
  nodeVersion: process.version,
  harnessDirty: process.env.QUNXIA_HARNESS_DIRTY === "1",
  gameApi: process.env.QUNXIA_API,
  scale: profileDefinition.scale,
  observeAfterAction: profileDefinition.observeAfterAction,
  extensions: profileDefinition.extensions,
  tools: profileDefinition.tools,
  prompt: promptMetadata,
  model: {
    ref: modelRef,
    provider: modelProvider,
    id: modelId,
    baseUrl: process.env.QUNXIA_LLM_BASE_URL,
    input,
    contextWindow,
    maxTokens,
    api,
    reasoning,
    supportsReasoningEffort,
    thinkingLevel,
    mappedThinkingLevel,
    thinkingLevelMap,
  },
};

const models = {
  providers: {
    [identity.model.provider]: {
      baseUrl: identity.model.baseUrl,
      api: identity.model.api,
      apiKey: "$QUNXIA_LLM_API_KEY",
      compat: api === "google-generative-ai" ? undefined : {
        supportsDeveloperRole: false,
        supportsReasoningEffort: identity.model.supportsReasoningEffort,
      },
      models: [{
        id: identity.model.id,
        name: identity.model.id,
        input: identity.model.input,
        contextWindow: identity.model.contextWindow,
        maxTokens: identity.model.maxTokens,
        reasoning: identity.model.reasoning,
        thinkingLevelMap: identity.model.thinkingLevelMap,
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      }],
    },
  },
};

if (resume) {
  const manifest = existingManifest;

  for (const field of [
    "runId",
    "profile",
    "piPackage",
    "piVersion",
    "nodeVersion",
    "gameApi",
    "scale",
    "observeAfterAction",
  ]) {
    if (manifest[field] !== identity[field]) {
      throw new Error(`cannot resume ${runId}: ${field} changed`);
    }
  }
  for (const field of ["extensions", "tools", "prompt"]) {
    if (JSON.stringify(manifest[field]) !== JSON.stringify(identity[field])) {
      throw new Error(`cannot resume ${runId}: ${field} changed`);
    }
  }
  if (JSON.stringify(manifest.model) !== JSON.stringify(identity.model)) {
    throw new Error(`cannot resume ${runId}: model configuration changed`);
  }

  process.stdout.write(`${runDir}\n`);
  process.exit(0);
}

try {
  await mkdir(runDir, { recursive: false, mode: 0o700 });
} catch (error) {
  if (error?.code === "EEXIST") {
    throw new Error(`run ${runId} already exists; set QUNXIA_RESUME=1 to continue it`);
  }
  await mkdir(dirname(runDir), { recursive: true, mode: 0o700 });
  await mkdir(runDir, { recursive: false, mode: 0o700 });
}

await Promise.all([
  mkdir(configDir, { mode: 0o700 }),
  mkdir(sessionDir, { mode: 0o700 }),
  mkdir(workspaceDir, { mode: 0o700 }),
]);

await writeFile(join(configDir, "SYSTEM.md"), systemPrompt, { mode: 0o600 });
if (benchmarkHelp !== null) {
  await writeFile(join(configDir, "benchmark-help.md"), benchmarkHelp, { mode: 0o600 });
}
await writeFile(join(configDir, "models.json"), `${JSON.stringify(models, null, 2)}\n`, { mode: 0o600 });
await writeFile(
  join(configDir, "profile.json"),
  `${JSON.stringify(profileDefinition, null, 2)}\n`,
  { mode: 0o600 },
);
for (const extension of profileDefinition.extensions) {
  await cp(join(root, "pi-agent", "extensions", extension), join(configDir, extension), {
    recursive: true,
  });
}
const manifest = {
  ...identity,
  createdAt: new Date().toISOString(),
  paths: {
    config: "config",
    sessions: "sessions",
    workspace: "workspace",
    help: benchmarkHelp !== null ? "config/benchmark-help.md" : null,
  },
};
await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, { mode: 0o600 });
process.stdout.write(`${runDir}\n`);

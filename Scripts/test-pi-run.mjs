import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
// Exercise the exact compatibility code bundled with the pinned Pi package.
import {
  clampThinkingLevel,
  getSupportedThinkingLevels,
  streamSimple,
} from "../node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/compat.js";

const root = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const prepare = join(root, "Scripts", "prepare-pi-run.mjs");
const readProfile = join(root, "Scripts", "read-pi-profile.mjs");
const playAgent = join(root, "Scripts", "play-agent.sh");
const benchmarkHelp = [
  "# Benchmark help fixture",
  "## API",
  "GET  http://game.invalid/api/screen look, pressing nothing",
  "POST http://game.invalid/api/key one key",
  "POST http://game.invalid/api/keys several keys",
  "POST http://game.invalid/api/wait let the game run",
  "## 移動：請用九宮數字鍵的名稱",
].join("\n");
const benchmarkHelpUrl = `data:text/plain;charset=utf-8,${encodeURIComponent(benchmarkHelp)}`;

function invoke(runsDir, runId, profile = "strict", resume = false, overrides = {}) {
  const runDir = join(runsDir, runId);
  return spawnSync(process.execPath, [prepare], {
    encoding: "utf8",
    env: {
      ...process.env,
      QUNXIA_ROOT: root,
      QUNXIA_RUN_DIR: runDir,
      QUNXIA_RUN_ID: runId,
      QUNXIA_PI_PROFILE: profile,
      QUNXIA_PI_VERSION: "0.84.4",
      QUNXIA_BENCH_LANG: "zh",
      QUNXIA_BENCH_HELP_URL: benchmarkHelpUrl,
      QUNXIA_LLM_BASE_URL: "http://model.invalid/v1",
      QUNXIA_MODEL_REF: "local-test/test-model",
      QUNXIA_MODEL_CONFIG: "",
      QUNXIA_LLM_INPUT_JSON: '["text","image"]',
      QUNXIA_LLM_CONTEXT: "128000",
      QUNXIA_LLM_MAX_TOKENS: "8192",
      QUNXIA_LLM_API: "openai-completions",
      QUNXIA_LLM_REASONING: "1",
      QUNXIA_LLM_SUPPORTS_REASONING_EFFORT: "1",
      QUNXIA_THINKING: profile === "benchmark" ? "high" : "",
      QUNXIA_API: "http://game.invalid",
      QUNXIA_HARNESS_DIRTY: "0",
      QUNXIA_RESUME: resume ? "1" : "0",
      ...overrides,
    },
  });
}

test("new runs have separate state and resolved profiles", async () => {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-pi-runs-"));
  for (const id of ["run-a", "run-b"]) {
    const result = invoke(runsDir, id);
    assert.equal(result.status, 0, result.stderr);
  }

  const a = JSON.parse(await readFile(join(runsDir, "run-a", "run.json"), "utf8"));
  const b = JSON.parse(await readFile(join(runsDir, "run-b", "run.json"), "utf8"));
  assert.notEqual(a.runId, b.runId);
  assert.equal(a.paths.help, null);
  assert.equal(a.scale, 1);
  assert.equal(a.observeAfterAction, true);
  assert.equal(a.model.thinkingLevel, "medium");
  assert.equal(a.model.ref, "local-test/test-model");
  assert.equal(a.model.provider, "local-test");
  assert.deepEqual(a.extensions, ["qunxia"]);
  assert.deepEqual(a.tools, [
    "game_look",
    "game_press",
    "game_press_sequence",
    "game_move",
    "game_wait",
    "game_save",
    "game_load",
    "game_saves",
  ]);
  const models = await readFile(join(runsDir, "run-a", "config", "models.json"), "utf8");
  assert.match(models, /\$QUNXIA_LLM_API_KEY/);
  const resolvedProfile = JSON.parse(
    await readFile(join(runsDir, "run-a", "config", "profile.json"), "utf8"),
  );
  assert.deepEqual(resolvedProfile.tools, a.tools);
});

test("existing runs require explicit compatible resume", async () => {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-pi-resume-"));
  assert.equal(invoke(runsDir, "resume-a").status, 0);

  const duplicate = invoke(runsDir, "resume-a");
  assert.notEqual(duplicate.status, 0);
  assert.match(duplicate.stderr, /already exists/);

  const resumed = invoke(runsDir, "resume-a", "strict", true);
  assert.equal(resumed.status, 0, resumed.stderr);
  const changedModel = invoke(runsDir, "resume-a", "strict", true, {
    QUNXIA_MODEL_REF: "local-test/different-model",
  });
  assert.notEqual(changedModel.status, 0);
  assert.match(changedModel.stderr, /model configuration changed/);

  const changedThinking = invoke(runsDir, "resume-a", "strict", true, {
    QUNXIA_THINKING: "high",
  });
  assert.notEqual(changedThinking.status, 0);
  assert.match(changedThinking.stderr, /model configuration changed/);
});

test("unknown profiles fail closed", async () => {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-pi-profile-"));
  const result = invoke(runsDir, "unknown-a", "not-a-profile");
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unknown QUNXIA_PI_PROFILE/);
});

test("profile lookup explains an unknown profile", () => {
  const result = spawnSync(process.execPath, [
    readProfile,
    join(root, "pi-agent", "profiles.json"),
    "not-a-profile",
  ], {
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unknown QUNXIA_PI_PROFILE not-a-profile/);
  assert.match(result.stderr, /available profiles:/);
});

test("the launcher requires a full provider/model reference", () => {
  const result = spawnSync("zsh", [playAgent], {
    encoding: "utf8",
    env: {
      ...process.env,
      QUNXIA_LLM_BASE_URL: "http://model.invalid/v1",
      QUNXIA_LLM_MODEL: "model-without-provider",
    },
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must include non-empty provider and model names/);
});

test("supplied benchmark APIs are probed through the public visual route", async () => {
  const launcher = await readFile(playAgent, "utf8");
  assert.match(launcher, /\/screen\?format=png&spectate=1/);
  assert.match(launcher, /BENCH_HELP_URL="\$API\/help\?lang=\$BENCH_LANG"/);
});

test("benchmark profile exposes only broker-supported game tools", async () => {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-pi-benchmark-"));
  const result = invoke(runsDir, "benchmark-a", "benchmark");
  assert.equal(result.status, 0, result.stderr);
  const manifest = JSON.parse(await readFile(join(runsDir, "benchmark-a", "run.json"), "utf8"));
  assert.deepEqual(manifest.tools, [
    "game_look",
    "game_press",
    "game_press_sequence",
    "game_wait",
  ]);
  assert.equal(manifest.scale, 1);
  assert.equal(manifest.observeAfterAction, false);
  assert.equal(manifest.prompt.source, "session-help");
  assert.equal(manifest.prompt.language, "zh");
  assert.equal(manifest.prompt.helpChars, benchmarkHelp.length);
  assert.equal(manifest.model.api, "openai-completions");
  assert.equal(manifest.model.reasoning, true);
  assert.equal(manifest.model.supportsReasoningEffort, true);
  assert.equal(manifest.model.thinkingLevel, "high");
  assert.equal(manifest.model.mappedThinkingLevel, "high");
  assert.deepEqual(manifest.model.thinkingLevelMap, {});
  const models = JSON.parse(
    await readFile(join(runsDir, "benchmark-a", "config", "models.json"), "utf8"),
  );
  const model = models.providers[manifest.model.provider].models[0];
  assert.ok(getSupportedThinkingLevels(model).includes("high"));
  assert.equal(clampThinkingLevel(model, "high"), "high");
  const prompt = await readFile(join(runsDir, "benchmark-a", "config", "SYSTEM.md"), "utf8");
  assert.match(prompt, /BEGIN SESSION-SPECIFIC BENCHMARK BRIEF/);
  assert.match(prompt, /character is already named/);
  assert.match(prompt, /POST http:\/\/game\.invalid\/api\/key/);
  assert.doesNotMatch(prompt, /\{BASE\}/);
  assert.doesNotMatch(prompt, /Entering a Chinese name/);
});

test("game press leaves the server tap duration authoritative", async () => {
  const extension = await readFile(
    join(root, "pi-agent", "extensions", "qunxia", "index.ts"),
    "utf8",
  );
  assert.match(extension, /Omit to use the game server's .*tap default/);
  assert.doesNotMatch(extension, /default 4/);
  assert.match(extension, /times: Type\.Optional\(Type\.Integer/);
  assert.match(extension, /maximum: 100, description: "Repeat count/);
  assert.match(extension, /const times = params\.times \?\? 1/);
  assert.match(extension, /const steps = params\.steps \?\? 1/);
  assert.doesNotMatch(extension, /boundedInteger/);
  assert.doesNotMatch(extension, /Frames to hold for long movement/);
  assert.match(extension, /res\.played_seconds \?\? res\.played/);
});

test("launcher accepts only Pi-supported non-RPC output modes", async () => {
  const launcher = await readFile(playAgent, "utf8");
  assert.match(launcher, /--mode must be text or json/);
  assert.match(launcher, /--mode=\.\.\. is not supported/);
});

test("benchmark documentation uses the session URL returned by the broker", async () => {
  const readme = await readFile(join(root, "README.md"), "utf8");
  assert.match(readme, /BASE_URL=.*\/s\/replace-with-the-created-session-id/);
  assert.match(readme, /QUNXIA_API="\$\{BASE_URL%\/\}\/api"/);
  assert.doesNotMatch(readme, /127\.0\.0\.1:8084\/u\//);
});

test("benchmark thinking must be explicit and supported", () => {
  const runsDir = join(tmpdir(), `qunxia-pi-thinking-${process.pid}-${Date.now()}`);
  const missing = invoke(runsDir, "missing-thinking", "benchmark", false, {
    QUNXIA_THINKING: "",
  });
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /explicit QUNXIA_THINKING/);

  const unsupported = invoke(runsDir, "unsupported-thinking", "benchmark", false, {
    QUNXIA_LLM_REASONING: "0",
  });
  assert.notEqual(unsupported.status, 0);
  assert.match(unsupported.stderr, /requires a reasoning model/);
});

test("benchmark profile fails closed without complete session help", async () => {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-pi-missing-help-"));
  const missing = invoke(runsDir, "missing-help", "benchmark", false, {
    QUNXIA_BENCH_HELP_URL: "",
  });
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /requires QUNXIA_BENCH_HELP_URL/);

  const incomplete = invoke(runsDir, "incomplete-help", "benchmark", false, {
    QUNXIA_BENCH_HELP_URL: "data:text/plain,incomplete",
  });
  assert.notEqual(incomplete.status, 0);
  assert.match(incomplete.stderr, /benchmark help is incomplete/);
});

const geminiDefinition = {
  id: "gemini-3.8-flash",
  api: "google-generative-ai",
  reasoning: true,
  input: ["text", "image"],
  contextWindow: 1048576,
  maxTokens: 65536,
  thinkingLevelMap: {
    off: null, minimal: null, low: "low", medium: "medium", high: "high",
    xhigh: null, max: null,
  },
};

async function prepareDefinedModel(definition, thinking, runId = "defined-model") {
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-model-definition-"));
  const definitionPath = join(runsDir, "model.json");
  await writeFile(definitionPath, JSON.stringify(definition));
  const overrides = {
    QUNXIA_MODEL_REF: `test-route/${definition.id}`,
    QUNXIA_MODEL_CONFIG: definitionPath,
    QUNXIA_THINKING: thinking,
    QUNXIA_LLM_API: "", QUNXIA_LLM_REASONING: "",
    QUNXIA_LLM_SUPPORTS_REASONING_EFFORT: "", QUNXIA_LLM_INPUT_JSON: "",
    QUNXIA_LLM_CONTEXT: "", QUNXIA_LLM_MAX_TOKENS: "",
  };
  return { runsDir, runId, overrides, result: invoke(runsDir, runId, "benchmark", false, overrides) };
}

test("Gemini definition survives isolation and produces native HIGH thinking", async () => {
  const { runsDir, runId, result, overrides } = await prepareDefinedModel(geminiDefinition, "high");
  assert.equal(result.status, 0, result.stderr);
  const runDir = join(runsDir, runId);
  const manifest = JSON.parse(await readFile(join(runDir, "run.json"), "utf8"));
  const config = JSON.parse(await readFile(join(runDir, "config", "models.json"), "utf8"));
  const provider = config.providers["test-route"];
  const model = { ...provider.models[0], provider: "test-route", api: provider.api, baseUrl: provider.baseUrl };
  assert.equal(model.api, "google-generative-ai");
  assert.deepEqual(getSupportedThinkingLevels(model), ["low", "medium", "high"]);
  assert.equal(manifest.model.thinkingLevel, "high");
  assert.equal(manifest.model.mappedThinkingLevel, "high");
  assert.equal(model.contextWindow, 1048576);
  assert.equal(model.maxTokens, 65536);
  assert.equal(provider.compat, undefined);
  let payload;
  await streamSimple(model, {
    messages: [{ role: "user", content: "test", timestamp: 0 }],
  }, {
    reasoning: manifest.model.thinkingLevel,
    apiKey: "fake-test-key",
    onPayload(value) { payload = value; throw new Error("captured before network"); },
  }).result();
  assert.equal(payload.config.thinkingConfig.thinkingLevel, "HIGH");
  assert.equal(payload.config.thinkingConfig.thinkingBudget, undefined);
  assert.equal(payload.config.maxOutputTokens, 65536);
  const resumed = invoke(runsDir, runId, "benchmark", true, {
    ...overrides, QUNXIA_MODEL_CONFIG: "", QUNXIA_THINKING: "",
  });
  assert.equal(resumed.status, 0, resumed.stderr);
});

test("unsupported Max is rejected rather than manufactured or silently reduced", async () => {
  const gemini = await prepareDefinedModel(geminiDefinition, "max");
  assert.notEqual(gemini.result.status, 0);
  assert.match(gemini.result.stderr, /unsupported thinking level max; supported: low, medium, high/);
  const runsDir = await mkdtemp(join(tmpdir(), "qunxia-no-max-"));
  const custom = invoke(runsDir, "custom", "benchmark", false, { QUNXIA_THINKING: "max" });
  assert.notEqual(custom.status, 0);
  assert.match(custom.stderr, /unsupported thinking level max/);
});

test("an explicitly defined Max-capable model sends the declared provider effort", async () => {
  const { runsDir, runId, result } = await prepareDefinedModel({
    id: "max-model", api: "openai-completions", reasoning: true,
    supportsReasoningEffort: true, thinkingLevelMap: { max: "max" },
  }, "max");
  assert.equal(result.status, 0, result.stderr);
  const config = JSON.parse(await readFile(join(runsDir, runId, "config", "models.json"), "utf8"));
  const provider = config.providers["test-route"];
  const model = { ...provider.models[0], api: provider.api, baseUrl: provider.baseUrl,
    provider: "test-route", compat: provider.compat };
  assert.equal(clampThinkingLevel(model, "max"), "max");
  let payload;
  await streamSimple(model, { messages: [{ role: "user", content: "test", timestamp: 0 }] }, {
    reasoning: "max", apiKey: "fake-test-key",
    onPayload(value) { payload = value; throw new Error("captured before network"); },
  }).result();
  assert.equal(payload.reasoning_effort, "max");
});

test("the manifest preserves an explicit off mapping without claiming a wire capture", async () => {
  const { runsDir, runId, result } = await prepareDefinedModel({
    id: "off-model", api: "openai-completions", reasoning: true,
    supportsReasoningEffort: true, thinkingLevelMap: { off: "none" },
  }, "off");
  assert.equal(result.status, 0, result.stderr);
  const manifest = JSON.parse(await readFile(join(runsDir, runId, "run.json"), "utf8"));
  assert.equal(manifest.model.thinkingLevel, "off");
  assert.equal(manifest.model.mappedThinkingLevel, "none");
  assert.equal("providerThinkingLevel" in manifest.model, false);
});

import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const pixel = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWZkAAAAASUVORK5CYII=";

test("isolated launcher preserves Gemini High through the real Pi CLI and HTTP adapter", { timeout: 60000 }, async t => {
  const directory = await mkdtemp(join(tmpdir(), "qunxia-cli-http-"));
  const requests = [];
  let base;
  const server = createServer(async (req, res) => {
    let text = "";
    for await (const chunk of req) text += chunk;
    requests.push({ path: req.url, body: text ? JSON.parse(text) : null });
    if (req.url.startsWith("/api/help")) {
      res.end(["# Fixture game brief", ...["screen", "key", "keys", "wait"].map(
        name => `${name === "screen" ? "GET" : "POST"} ${base}/api/${name}`,
      )].join("\n"));
    } else if (req.url.startsWith("/api/screen")) {
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ ok: true, image: pixel, width: 1, height: 1 }));
    } else if (req.url.includes(":streamGenerateContent")) {
      res.setHeader("Content-Type", "text/event-stream");
      res.end(`data: ${JSON.stringify({ candidates: [{ content: { role: "model", parts: [{ text: "Fixture finished." }] }, finishReason: "STOP" }], usageMetadata: { promptTokenCount: 100, candidatesTokenCount: 20, totalTokenCount: 120 } })}\n\n`);
    } else {
      res.writeHead(404).end();
    }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  t.after(() => { server.closeAllConnections(); server.close(); });
  const definition = join(directory, "gemini.json");
  await writeFile(definition, JSON.stringify({
    id: "gemini-3.8-flash", api: "google-generative-ai", reasoning: true,
    input: ["text", "image"], contextWindow: 1048576, maxTokens: 65536,
    thinkingLevelMap: { off: null, minimal: null, low: "low", medium: "medium", high: "high", xhigh: null, max: null },
  }));
  const env = {
    ...Object.fromEntries(Object.entries(process.env).filter(([name]) => !name.startsWith("QUNXIA_"))),
    PATH: `${dirname(process.execPath)}:${process.env.PATH}`,
    QUNXIA_LLM_MODEL: "fixture-google/gemini-3.8-flash", QUNXIA_LLM_BASE_URL: `${base}/v1beta`,
    QUNXIA_LLM_API_KEY: "fake-test-key", QUNXIA_MODEL_CONFIG: definition,
    QUNXIA_THINKING: "high", QUNXIA_PI_PROFILE: "benchmark", QUNXIA_API: `${base}/api`,
    QUNXIA_RUNS_DIR: directory, QUNXIA_RUN_ID: "high-run",
  };
  const child = spawn("zsh", [join(root, "Scripts", "play-agent.sh"), "-p", "Reply briefly."], {
    env, cwd: root, stdio: ["ignore", "pipe", "pipe"],
  });
  t.after(() => { if (child.exitCode === null) child.kill(); });
  let output = "";
  child.stdout.on("data", data => { output += data; });
  child.stderr.on("data", data => { output += data; });
  const status = await new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", resolve);
  });
  assert.equal(status, 0, output);
  const calls = requests.filter(req => req.path.includes(":streamGenerateContent"));
  assert.equal(calls.length, 1, output);
  const body = calls[0].body;
  assert.equal(body.generationConfig.thinkingConfig.thinkingLevel, "HIGH");
  assert.equal(body.generationConfig.thinkingConfig.thinkingBudget, undefined);
  assert.equal(body.generationConfig.maxOutputTokens, 65536);
  assert.match(JSON.stringify(body.systemInstruction), /Fixture game brief/);
  const names = body.tools.flatMap(group => (group.functionDeclarations ?? []).map(tool => tool.name));
  assert.deepEqual(names.sort(), ["game_look", "game_press", "game_press_sequence", "game_wait"]);
  const manifest = JSON.parse(await readFile(join(directory, "high-run", "run.json"), "utf8"));
  assert.equal(manifest.model.thinkingLevel, "high");
  assert.equal(manifest.model.mappedThinkingLevel, "high");
  assert.equal(manifest.model.api, "google-generative-ai");

  // The harness meters what the provider billed: the session's usage,
  // captured after the run ends and kept with the run's other artifacts.
  const usage = JSON.parse(await readFile(join(directory, "high-run", "usage.json"), "utf8"));
  assert.equal(usage.turns, 1);
  assert.equal(usage.input, 100);
  assert.equal(usage.output, 20);
  assert.equal(usage.totalTokens, 120);
  // Without a benchmark agent name there is nothing to publish: the capture
  // stays a local artifact and the broker is never contacted.
  assert.equal(requests.filter(req => req.url === "/usage").length, 0);
});

test("extension game tools execute against the game API through the real Pi CLI", { timeout: 60000 }, async t => {
  const directory = await mkdtemp(join(tmpdir(), "qunxia-tool-call-"));
  const requests = [];
  let base;
  const server = createServer(async (req, res) => {
    let text = "";
    for await (const chunk of req) text += chunk;
    requests.push({ path: req.url, body: text ? JSON.parse(text) : null, xAgent: req.headers["x-agent"] });
    if (req.url === "/usage") {
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ ok: true, merged: true }));
    } else if (req.url.startsWith("/api/help")) {
      res.end(["# Fixture game brief", ...["screen", "key", "keys", "wait"].map(
        name => `${name === "screen" ? "GET" : "POST"} ${base}/api/${name}`,
      )].join("\n"));
    } else if (req.url.startsWith("/api/screen")) {
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ ok: true, image: pixel, width: 1, height: 1 }));
    } else if (req.url.includes(":streamGenerateContent")) {
      // First turn: the model calls the look tool. Second turn: it finishes.
      const turn = requests.filter(r => r.path.includes(":streamGenerateContent")).length;
      const parts = turn === 1
        ? [{ functionCall: { name: "game_look", args: {} } }]
        : [{ text: "Fixture finished." }];
      res.setHeader("Content-Type", "text/event-stream");
      res.end(`data: ${JSON.stringify({ candidates: [{ content: { role: "model", parts }, finishReason: "STOP" }], usageMetadata: { promptTokenCount: 100, candidatesTokenCount: 20, totalTokenCount: 120 } })}\n\n`);
    } else {
      res.writeHead(404).end();
    }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  t.after(() => { server.closeAllConnections(); server.close(); });
  const definition = join(directory, "gemini.json");
  await writeFile(definition, JSON.stringify({
    id: "gemini-3.8-flash", api: "google-generative-ai", reasoning: true,
    input: ["text", "image"], contextWindow: 1048576, maxTokens: 65536,
    thinkingLevelMap: { off: null, minimal: null, low: "low", medium: "medium", high: "high", xhigh: null, max: null },
  }));
  const env = {
    ...Object.fromEntries(Object.entries(process.env).filter(([name]) => !name.startsWith("QUNXIA_"))),
    PATH: `${dirname(process.execPath)}:${process.env.PATH}`,
    QUNXIA_LLM_MODEL: "fixture-google/gemini-3.8-flash", QUNXIA_LLM_BASE_URL: `${base}/v1beta`,
    QUNXIA_LLM_API_KEY: "fake-test-key", QUNXIA_MODEL_CONFIG: definition,
    QUNXIA_THINKING: "high", QUNXIA_PI_PROFILE: "benchmark", QUNXIA_API: `${base}/api`,
    QUNXIA_RUNS_DIR: directory, QUNXIA_RUN_ID: "tool-call-run",
    QUNXIA_BENCH_AGENT: "fixture-agent",
  };
  const child = spawn("zsh", [join(root, "Scripts", "play-agent.sh"), "-p", "Look at the screen."], {
    env, cwd: root, stdio: ["ignore", "pipe", "pipe"],
  });
  t.after(() => { if (child.exitCode === null) child.kill(); });
  let output = "";
  child.stdout.on("data", data => { output += data; });
  child.stderr.on("data", data => { output += data; });
  const status = await new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", resolve);
  });
  assert.equal(status, 0, output);

  // The extension names the run in the activity log, like every other harness.
  const toolScreens = requests.filter(req => req.path.startsWith("/api/screen") && req.xAgent);
  assert.equal(toolScreens.length, 1, output);
  assert.equal(toolScreens[0].xAgent, "pi");

  // The model's tool call executed against the game API and came back as a
  // clean result: the status line and the frame, not a harness error.
  const calls = requests.filter(req => req.path.includes(":streamGenerateContent"));
  assert.equal(calls.length, 2, output);
  const parts = calls[1].body.contents.flatMap(content => content.parts ?? []);
  const result = parts.find(part => part.functionResponse?.name === "game_look");
  assert.ok(result, output);
  assert.equal(result.functionResponse.response.error, undefined);
  assert.match(JSON.stringify(result.functionResponse.response), /look \\| 1x1/);

  // The usage report is the provider's meter from both turns, named for the
  // agent the run was created under, and it lands on the run's session base.
  const usageJson = JSON.parse(await readFile(join(directory, "tool-call-run", "usage.json"), "utf8"));
  assert.equal(usageJson.turns, 2);
  assert.equal(usageJson.totalTokens, 240);
  const reports = requests.filter(req => req.path === "/usage");
  assert.equal(reports.length, 1, output);
  assert.equal(reports[0].xAgent, "fixture-agent");
  assert.equal(reports[0].body.turns, 2);
  assert.equal(reports[0].body.totalTokens, 240);
  assert.equal(reports[0].body.model, "fixture-google/gemini-3.8-flash");
});

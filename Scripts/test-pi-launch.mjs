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
      res.end(`data: ${JSON.stringify({ candidates: [{ content: { role: "model", parts: [{ text: "Fixture finished." }] }, finishReason: "STOP" }] })}\n\n`);
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
});

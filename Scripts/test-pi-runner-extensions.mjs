// The two extensions bench_jobs.py loads into pi, run through the real pi CLI
// against a fixture model. PI selects the pi binary (default: pi on PATH, the
// one the runner uses).
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readdir, readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { crc32, deflateSync } from "node:zlib";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const SEQUENTIAL = join(root, "Scripts", "pi-sequential-tools.ts");
const WINDOW = join(root, "Scripts", "pi-image-window.ts");
const NOTE = "(earlier image omitted from this request)";
// A 32x20 RGB PNG, the shape of a small game frame; shade tells frames apart.
function png(shade) {
  const chunk = (type, data) => {
    const body = Buffer.concat([Buffer.from(type), data]);
    const out = Buffer.alloc(body.length + 8);
    out.writeUInt32BE(data.length, 0);
    body.copy(out, 4);
    out.writeUInt32BE(crc32(body), body.length + 4);
    return out;
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(32, 0);
  header.writeUInt32BE(20, 4);
  header.set([8, 2, 0, 0, 0], 8);
  const row = Buffer.concat([Buffer.from([0]), Buffer.alloc(32 * 3, shade)]);
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", header),
    chunk("IDAT", deflateSync(Buffer.concat(Array(20).fill(row)))), chunk("IEND", Buffer.alloc(0))]);
}

// An OpenAI-compatible model that answers request n with turns[n] (a list of
// tool calls, or a string) and records every request body.
async function fixtureModel(t, turns) {
  const requests = [];
  const server = createServer(async (req, res) => {
    let text = "";
    for await (const chunk of req) text += chunk;
    const body = JSON.parse(text);
    requests.push(body);
    const turn = turns[Math.min(requests.length, turns.length) - 1];
    const delta = typeof turn === "string"
      ? { role: "assistant", content: turn }
      : { role: "assistant", tool_calls: turn.map(([name, args], index) => ({
          index, id: `call_${requests.length}_${index}`, type: "function",
          function: { name, arguments: JSON.stringify(args) } })) };
    const chunk = (choice, extra = {}) =>
      `data: ${JSON.stringify({ id: "fx", object: "chat.completion.chunk", created: 0,
        model: "fixture", choices: [choice], ...extra })}\n\n`;
    res.setHeader("Content-Type", "text/event-stream");
    res.end(chunk({ index: 0, delta, finish_reason: null })
      + chunk({ index: 0, delta: {}, finish_reason: typeof turn === "string" ? "stop" : "tool_calls" },
        { usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 } })
      + "data: [DONE]\n\n");
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  return { requests, base: `http://127.0.0.1:${server.address().port}/v1` };
}

async function runPi(t, base, extensions, work) {
  const agentDir = await mkdtemp(join(tmpdir(), "pi-agent-"));
  await writeFile(join(agentDir, "models.json"), JSON.stringify({ providers: { fixture: {
    baseUrl: base, api: "openai-completions", apiKey: "fixture-key",
    models: [{ id: "fixture", input: ["text", "image"], contextWindow: 200000, maxTokens: 4096 }],
  } } }));
  const args = ["--no-extensions", "--no-skills", "--no-prompt-templates", "--no-context-files",
    "--no-themes", "--offline", ...extensions.flatMap(e => ["-e", e]),
    "--session-dir", join(agentDir, "sessions"), "--model", "fixture/fixture",
    "--mode", "json", "-p", "Play."];
  const child = spawn(process.env.PI || "pi", args, {
    cwd: work, env: { ...process.env, PI_CODING_AGENT_DIR: agentDir, PI_OFFLINE: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  t.after(() => { if (child.exitCode === null) child.kill(); });
  let output = "";
  child.stdout.on("data", d => { output += d; });
  child.stderr.on("data", d => { output += d; });
  const status = await new Promise((resolve, reject) => { child.on("error", reject); child.on("exit", resolve); });
  assert.equal(status, 0, output);
  return agentDir;
}

// What the read call answered, as the model saw it in the next request.
function readResult(body) {
  const tool = body.messages.filter(m => m.role === "tool").at(-1);
  return typeof tool.content === "string" ? tool.content : JSON.stringify(tool.content);
}

// A key press and a screenshot read sent together, as the Claude models did.
const PRESS_AND_LOOK = [
  [["bash", { command: "sleep 1; echo after > screen.txt" }], ["read", { path: "screen.txt" }]],
  "done",
];

test("without the sequential tools, a read sent with a bash runs before it finishes", { timeout: 60000 }, async t => {
  // Positive control: proves the fixture reproduces the race the fix removes.
  const work = await mkdtemp(join(tmpdir(), "pi-work-"));
  await writeFile(join(work, "screen.txt"), "before\n");
  const { requests, base } = await fixtureModel(t, PRESS_AND_LOOK);
  await runPi(t, base, [WINDOW], work);
  assert.equal(requests.length, 2);
  assert.match(readResult(requests[1]), /before/);
});

test("with the sequential tools, a read sent with a bash sees what the bash wrote", { timeout: 60000 }, async t => {
  const work = await mkdtemp(join(tmpdir(), "pi-work-"));
  await writeFile(join(work, "screen.txt"), "before\n");
  const { requests, base } = await fixtureModel(t, PRESS_AND_LOOK);
  await runPi(t, base, [WINDOW, SEQUENTIAL], work);
  assert.equal(requests.length, 2);
  assert.match(readResult(requests[1]), /after/);
  // The model is offered the same four tools under the same names.
  assert.deepEqual(requests[0].tools.map(x => x.function.name).sort(), ["bash", "edit", "read", "write"]);
});

test("the image window sends the latest turn's images and the four before them", { timeout: 60000 }, async t => {
  const work = await mkdtemp(join(tmpdir(), "pi-work-"));
  await mkdir(join(work, "f"));
  for (let i = 0; i < 9; i++) await writeFile(join(work, "f", `${i}.png`), png(20 * i));
  // Seven turns of one screenshot each, then one turn that reads two together.
  const turns = [...Array(7).keys()].map(i => [["read", { path: `f/${i}.png` }]]);
  turns.push([["read", { path: "f/7.png" }], ["read", { path: "f/8.png" }]], "done");
  const { requests, base } = await fixtureModel(t, turns);
  const agentDir = await runPi(t, base, [WINDOW, SEQUENTIAL], work);
  assert.equal(requests.length, 9);
  const count = (body, needle) => JSON.stringify(body).split(needle).length - 1;
  // Request n carries the n images read so far, at most 2 (latest turn) + 4.
  for (let n = 1; n < 9; n++) {
    const seen = n <= 7 ? n : 9;
    const latest = n <= 7 ? 1 : 2;
    const sent = Math.min(seen, latest + 4);
    assert.equal(count(requests[n], "data:image/png"), sent, `request ${n}`);
    assert.equal(count(requests[n], NOTE), seen - sent, `request ${n}`);
  }
  // Only the requests are trimmed: the session file keeps all nine images.
  const sessions = join(agentDir, "sessions");
  const files = await readdir(sessions);
  assert.equal(files.length, 1);
  assert.equal((await readFile(join(sessions, files[0]), "utf8")).split('"type":"image"').length - 1, 9);
});

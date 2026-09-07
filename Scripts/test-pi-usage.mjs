import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { access, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const script = join(root, "Scripts", "pi-usage.mjs");

const usage = (input, output, total, cost) => ({
  input, output, cacheRead: 0, cacheWrite: 0, totalTokens: total,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: cost },
});

const message = (id, parentId, role, body) => ({
  type: "message", id, parentId, timestamp: "2026-09-07T12:00:00.000Z",
  message: role === "assistant"
    ? { role, content: [], model: "provider/model-x", provider: "provider",
        api: "google-generative-ai", ...body, stopReason: "stop" }
    : { role, content: [{ type: "text", text: "turn" }] },
});

function runPiUsage(runDir) {
  return new Promise(resolve => {
    execFile(process.execPath, [script, runDir], (error, stdout, stderr) => {
      resolve({ code: error ? (typeof error.code === "number" ? error.code : 1) : 0,
                stdout, stderr });
    });
  });
}

async function makeRun(entries, extra = {}) {
  const runDir = await mkdtemp(join(tmpdir(), "qunxia-usage-"));
  await mkdir(join(runDir, "sessions"), { recursive: true });
  await writeFile(join(runDir, "sessions", "2026-09-07T12-00-00-000Z_test.jsonl"),
    extra.lines ?? entries.map(entry => `${JSON.stringify(entry)}\n`).join(""));
  if (extra.manifest) {
    await writeFile(join(runDir, "run.json"), JSON.stringify(extra.manifest));
  }
  return runDir;
}

test("the active branch is metered, including a compaction on it", async () => {
  const entries = [
    { type: "session", id: "s1", version: "0.84.4",
      timestamp: "2026-09-07T12:00:00.000Z", cwd: "/work" },
    message("u1", null, "user"),
    message("a1", "u1", "assistant", { usage: usage(10, 2, 16, 0.001) }),
    { type: "compaction", id: "c1", parentId: "a1",
      timestamp: "2026-09-07T12:01:00.000Z", summary: "so far" },
    message("u2", "c1", "user"),
    message("a2", "u2", "assistant", { usage: usage(100, 5, 105, 0.002) }),
  ];
  const runDir = await makeRun(entries, {
    manifest: { model: { ref: "provider/model-x" }, piVersion: "0.84.4" },
  });
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 0);
  const usageJson = JSON.parse(await readFile(join(runDir, "usage.json"), "utf8"));
  assert.equal(usageJson.turns, 2);
  assert.equal(usageJson.input, 110);
  assert.equal(usageJson.output, 7);
  assert.equal(usageJson.totalTokens, 121);
  assert.equal(usageJson.cost, 0.003);
  assert.equal(usageJson.session, "s1");
  assert.equal(usageJson.model, "provider/model-x");
  assert.equal(usageJson.piVersion, "0.84.4");
});

test("a discarded branch is not billed to the run", async () => {
  const entries = [
    { type: "session", id: "s1", version: "0.84.4",
      timestamp: "2026-09-07T12:00:00.000Z", cwd: "/work" },
    message("u1", null, "user"),
    message("a1", "u1", "assistant", { usage: usage(50, 5, 55, 0.005) }),
    message("u2", "a1", "user"),
    message("a2", "u2", "assistant", { usage: usage(10, 1, 11, 0.001) }),
    // An edited-out answer to the same user turn: written, then replaced.
    message("a3", "u2", "assistant", { usage: usage(999, 9, 1008, 0.1) }),
  ];
  const runDir = await makeRun(entries);
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 0);
  const usageJson = JSON.parse(await readFile(join(runDir, "usage.json"), "utf8"));
  // Only a1 and a3 are on the live branch: the run is billed for the answer
  // it actually used, never for the one that was edited away.
  assert.equal(usageJson.turns, 2);
  assert.equal(usageJson.input, 1049);
  assert.equal(usageJson.output, 14);
  assert.equal(usageJson.totalTokens, 1063);
  assert.equal(usageJson.cost, 0.105);
});

test("a torn final line is tolerated, a torn earlier line is not", async () => {
  const entries = [
    { type: "session", id: "s1", version: "0.84.4",
      timestamp: "2026-09-07T12:00:00.000Z", cwd: "/work" },
    message("u1", null, "user"),
    message("a1", "u1", "assistant", { usage: usage(7, 1, 8, 0) }),
  ];
  const full = entries.map(entry => JSON.stringify(entry)).join("\n");
  const torn = "\n" + '{"type":"message","id":"a2","parent';
  const runDir = await makeRun(entries, { lines: full + torn + "\n" });
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 0);
  const usageJson = JSON.parse(await readFile(join(runDir, "usage.json"), "utf8"));
  assert.equal(usageJson.turns, 1);
  assert.equal(usageJson.input, 7);

  const broken = await makeRun(entries, {
    lines: full.slice(0, 40) + "\n{not json}\n" + full.slice(40),
  });
  const brokenResult = await runPiUsage(broken);
  assert.notEqual(brokenResult.code, 0);
  await assert.rejects(access(join(broken, "usage.json")));
});

test("a run whose provider never metered its turns publishes nothing", async () => {
  // Pi writes usage only when the provider reported usageMetadata. Without
  // it every total is zero - and the board must show a dash, never a zero.
  const entries = [
    { type: "session", id: "s1", version: "0.84.4",
      timestamp: "2026-09-07T12:00:00.000Z", cwd: "/work" },
    message("u1", null, "user"),
    message("a1", "u1", "assistant"),
    message("u2", "a1", "user"),
    message("a2", "u2", "assistant"),
  ];
  const runDir = await makeRun(entries);
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 3);
  await assert.rejects(access(join(runDir, "usage.json")));
});

test("a run metered only in part publishes nothing", async () => {
  // A total that stops counting mid-run is an undercount, not a meter.
  const entries = [
    { type: "session", id: "s1", version: "0.84.4",
      timestamp: "2026-09-07T12:00:00.000Z", cwd: "/work" },
    message("u1", null, "user"),
    message("a1", "u1", "assistant", { usage: usage(10, 2, 12, 0) }),
    message("u2", "a1", "user"),
    message("a2", "u2", "assistant"),
  ];
  const runDir = await makeRun(entries);
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 3);
  await assert.rejects(access(join(runDir, "usage.json")));
});

test("a run without a session meters nothing and exits 3", async () => {
  const runDir = await mkdtemp(join(tmpdir(), "qunxia-usage-empty-"));
  const { code } = await runPiUsage(runDir);
  assert.equal(code, 3);
  await assert.rejects(access(join(runDir, "usage.json")));
});

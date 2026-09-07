#!/usr/bin/env node
// Capture the model usage of a Pi run from its session file.
//
// Pi persists every assistant turn's provider-reported usage into the session
// JSONL under the run's session dir. That is the provider's meter, not the
// model's claim, so it is a fair number to publish.
//
// A session is a tree: edited or retried turns branch off it. The active run
// is the path from the root to the leaf, and only that path is this run.
// Summing every entry would bill the run for discarded branches, so walk the
// leaf's parent chain and sum what lives on it.
//
//   node Scripts/pi-usage.mjs <run-dir>
//
// Reads <run-dir>/sessions/*.jsonl (the newest) and <run-dir>/run.json,
// writes <run-dir>/usage.json, and prints it. Exits 3 when there is nothing
// to publish: no session file yet, or the provider did not meter every
// assistant turn on the active branch (a total with a hole in it is not
// the run's usage). Exits non-zero on a corrupt file.

import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

const runDir = process.argv[2];
if (!runDir) {
  console.error("usage: pi-usage.mjs <run-dir>");
  process.exit(2);
}

const sessionsDir = join(runDir, "sessions");
let names;
try {
  names = await readdir(sessionsDir);
} catch {
  process.exit(3); // no session dir yet: pi never started a session
}
const jsonl = names.filter((name) => name.endsWith(".jsonl"));
if (jsonl.length === 0) process.exit(3);
// A resumed run appends to its file; the newest file is the active one.
jsonl.sort();
const sessionFile = join(sessionsDir, jsonl[jsonl.length - 1]);

const lines = (await readFile(sessionFile, "utf8")).split("\n").filter(Boolean);
if (lines.length === 0) {
  console.error(`session file ${sessionFile} is empty`);
  process.exit(1);
}
let sessionId = null;
const entries = new Map();
let leaf = null;
let t0 = null;
for (const [index, line] of lines.entries()) {
  let entry;
  try {
    entry = JSON.parse(line);
  } catch {
    if (index === lines.length - 1) continue; // torn last line: pi died mid-write
    throw new Error(`corrupt session entry at line ${index + 1}`);
  }
  if (entry.type === "session") {
    sessionId = entry.id;
    continue;
  }
  entries.set(entry.id, entry);
  leaf = entry; // append order is write order: the last entry is the live leaf
  if (t0 === null && entry.timestamp) t0 = Date.parse(entry.timestamp);
}
if (leaf === null) {
  console.error(`session file ${sessionFile} has no entries`);
  process.exit(1);
}

const totals = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: 0 };
let turns = 0;
let metered = 0;
const seen = new Set();
let cursor = leaf;
while (cursor && !seen.has(cursor.id)) {
  seen.add(cursor.id);
  if (cursor.type === "message" && cursor.message?.role === "assistant") {
    turns += 1;
    // Pi writes usage only when the provider metered the turn; a turn
    // without it is not a zero, it is a hole in the meter.
    const usage = cursor.message.usage;
    if (usage === undefined) continue;
    metered += 1;
    totals.input += usage.input ?? 0;
    totals.output += usage.output ?? 0;
    totals.cacheRead += usage.cacheRead ?? 0;
    totals.cacheWrite += usage.cacheWrite ?? 0;
    totals.totalTokens += usage.totalTokens
      ?? ((usage.input ?? 0) + (usage.output ?? 0)
          + (usage.cacheRead ?? 0) + (usage.cacheWrite ?? 0));
    totals.cost += usage.cost?.total ?? 0;
  }
  cursor = cursor.parentId ? entries.get(cursor.parentId) : null;
}

if (metered !== turns) {
  // No turn was metered, or only some were: publishing the total would put
  // a number on the board that is not a measurement of this run. The
  // catalogue entry keeps no usage and the site shows a dash.
  process.exit(3);
}

let model = null;
let piVersion = null;
try {
  const manifest = JSON.parse(await readFile(join(runDir, "run.json"), "utf8"));
  model = manifest.model?.ref ?? null;
  piVersion = manifest.piVersion ?? null;
} catch {
  // A usage capture without a manifest is still worth keeping.
}

const usage = {
  ...totals,
  cost: Math.round(totals.cost * 1e6) / 1e6,
  turns,
  model,
  piVersion,
  session: sessionId,
  capturedAt: new Date().toISOString(),
};
await writeFile(join(runDir, "usage.json"), `${JSON.stringify(usage, null, 2)}\n`, { mode: 0o600 });
process.stdout.write(`${JSON.stringify(usage)}\n`);

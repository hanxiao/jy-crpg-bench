#!/usr/bin/env node
import { readFileSync } from "node:fs";


const [profileFile, name] = process.argv.slice(2);
if (!profileFile || !name) {
  console.error("usage: read-pi-profile.mjs <profiles.json> <profile>");
  process.exit(2);
}

const profiles = JSON.parse(readFileSync(profileFile, "utf8"));
const profile = profiles[name];
if (!profile) {
  console.error(
    `unknown QUNXIA_PI_PROFILE ${name}; available profiles: ${Object.keys(profiles).join(", ")}`,
  );
  process.exit(1);
}
process.stdout.write(profile.prompt);
